"""Run the release gate with the published 1.2.1 wheel and two data directories.
Returns nonzero on ANY failed gate, including an explicitly forced downgrade.
Only the optional --public read contacts the real data endpoint. All writes
target a temporary client installation, loopback publisher and private caches.
"""
import argparse, functools, hashlib, json, os, runpy, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

HERE = Path(__file__).resolve()
MATRIX = HERE.parents[1] / "tests/test_baltic_containment.py"
SHA = "63ca42b44c2ba28ebc11f7bee8f42f624c72a61091831e8e94edb440b99ce7bc"
PUBLIC = "https://raw.githubusercontent.com/AION-Analytics-India/aion-market-calendar-data/main/lt"
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def worker(site, action):
    sys.path.insert(0, site)
    from importlib.metadata import version
    import aion_lithuanian_market_calendar as lib
    assert Path(lib.__file__).resolve().is_relative_to(site)
    assert version("aion-lithuanian-market-calendar") == "1.2.1"
    assert os.environ["AION_LT_CALENDAR_OFFLINE"] == "1"
    def guard(event, args):
        if os.environ["AION_LT_CALENDAR_OFFLINE"] == "1" and event in ("socket.connect", "socket.getaddrinfo"):
            raise AssertionError("unexpected offline network: " + event)
    sys.addaudithook(guard)
    before = lib.data_status()["dataset_version"]
    if action != "offline":
        os.environ["AION_LT_CALENDAR_OFFLINE"] = "0"
    result = lib.refresh_data(force=action in ("force", "offline", "public", "corrupt"))
    os.environ["AION_LT_CALENDAR_OFFLINE"] = "1"
    after = lib.data_status()["dataset_version"]
    row = dict(before=before, result=result, after=after, remote=lib.store.REMOTE_BASE)
    if action in ("baseline", "candidate", "offline"):
        row.update(runpy.run_path(str(MATRIX))["measurements"](action != "baseline"))
    print(json.dumps(row))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("wheel", "baseline", "candidate", "receipt"):
        p.add_argument("--" + k, required=True, type=Path)
    p.add_argument("--public", action="store_true")
    args = p.parse_args()
    assert sha(args.wheel) == SHA
    r = dict(wheel_sha256=SHA, utc=datetime.now(timezone.utc).isoformat(), generations={})
    versions = {}
    objects = {}
    for k, d in (("baseline", args.baseline), ("candidate", args.candidate)):
        m = json.loads((d/"manifest.json").read_bytes())
        assert {f: sha(d/f) for f in m["files"]} == m["files"]
        r["generations"][k] = {"manifest_sha256": sha(d/"manifest.json"), **m}
        versions[k] = m["dataset_version"]
        objects[k] = json.loads((d/"holidays_2026.json").read_bytes())
    assert r["generations"]["baseline"]["files"]["holidays_2026.json"] == "c79a98a028a81adccabb9ae86e51b0bc45af2481a3e3f1155c1b826307207de8"
    assert r["generations"]["baseline"]["files"]["holidays_2027.json"] == r["generations"]["candidate"]["files"]["holidays_2027.json"]
    mic_fields = {"exchange_holidays_by_venue", "half_days_by_venue"}
    assert {k for k in objects["candidate"].keys() | objects["baseline"].keys()
            if objects["candidate"].get(k) != objects["baseline"].get(k)} == mic_fields
    for key in mic_fields:
        a, b = (objects[n][key] for n in ("baseline", "candidate"))
        assert a.keys() == b.keys()
        assert {m for m in a if a[m] != b[m]} == {"XVIL", "XRIS", "XTAL"}
    assert all(objects["candidate"]["half_days_by_venue"][m] == {} for m in ("XVIL", "XRIS", "XTAL"))
    r["legacy_global_fields_unchanged"] = True
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp).resolve()
        site = t/"wheel-site"
        subprocess.run([sys.executable, "-m", "pip", "--isolated", "--disable-pip-version-check",
                        "install", "--target", str(site), "--no-compile", "--no-index", "--no-deps",
                        str(args.wheel.resolve())], check=True)
        for name, src in (("baseline", args.baseline), ("candidate", args.candidate), ("corrupt", args.candidate)):
            shutil.copytree(src, t/"public"/name)
        (t/"public/corrupt/holidays_2026.json").write_bytes(b"{}")
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        with ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(t/"public"))) as srv:
            th = Thread(target=srv.serve_forever, daemon=True)
            th.start()
            def read(name, cache, action):
                env = {**os.environ, "AION_LT_CALENDAR_CACHE": str(cache), "AION_LT_CALENDAR_OFFLINE": "1",
                       "AION_LT_CALENDAR_URL": f"http://127.0.0.1:{srv.server_port}/{name}",
                       "NO_PROXY":"127.0.0.1", "no_proxy":"127.0.0.1"}
                if action == "public":
                    env.pop("AION_LT_CALENDAR_URL")
                    for key in ("NO_PROXY", "no_proxy"):
                        if key in os.environ:
                            env[key] = os.environ[key]
                        else:
                            env.pop(key, None)
                proc = subprocess.run([sys.executable, "-I", str(HERE), "_worker", str(site), action],
                                      cwd=t, env=env, check=True, text=True, stdout=subprocess.PIPE, timeout=90)
                return json.loads(proc.stdout)
            try:
                baseline = read("baseline", t/"ref", "baseline")
                assert baseline["after"] == versions["baseline"]
                # Start a fresh interpreter on an already-adopted production-format cache.
                shutil.copytree(args.baseline, t/"cache")
                candidate = read("candidate", t/"cache", "candidate")
                assert (candidate["before"], candidate["after"]) == (versions["baseline"], versions["candidate"])
                assert candidate["non_baltic_sha256"] == baseline["non_baltic_sha256"], "Non-Baltic drift: stop"
                r["baseline"], r["candidate"] = baseline, candidate
                off = read("corrupt", t/"cache", "offline")
                assert off["before"] == off["after"] == versions["candidate"] and off["result"].startswith("offline")
                assert off["samples"] == candidate["samples"] and off["non_baltic_sha256"] == candidate["non_baltic_sha256"]
                r["offline_and_new_interpreter"] = {k:off[k] for k in ("before","after","result")}
                for name, endpoint, action in (("normal_downgrade","baseline","normal"),
                                               ("forced_downgrade","baseline","force"),
                                               ("corrupt_payload","corrupt","corrupt")):
                    cache = t/name
                    shutil.copytree(args.candidate, cache)
                    r[name] = read(endpoint, cache, action)
                assert r["corrupt_payload"]["after"] == versions["candidate"] and "verification failed" in r["corrupt_payload"]["result"]
                assert r["normal_downgrade"]["after"] == versions["candidate"]
                if args.public:
                    r["public"] = read(None, t/"clean-public", "public")
                    assert r["public"]["remote"] == PUBLIC
            finally:
                srv.shutdown()
                th.join()
    r["forced_downgrade_refused"] = r["forced_downgrade"]["after"] == versions["candidate"]
    args.receipt.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Receipt:", args.receipt, "forced downgrade refused:", r["forced_downgrade_refused"])
    return 0 if r["forced_downgrade_refused"] else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["_worker"]:
        worker(*sys.argv[2:])
    else:
        sys.exit(main())
