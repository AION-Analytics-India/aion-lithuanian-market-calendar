# Managed software updates: review candidate only

1.2.1 does not include this controller. Upgrading once does not enroll an application. No production trust policy, channel, validated wheelhouse or activation is supplied. Do not use a test key to enroll a customer.

For a disposable trial, install the **review wheel** with its `updates` extra. The maintainer supplies an independently authenticated bootstrap manifest, its SHA-256, a closed wheelhouse and a policy with an offline-root public key and HTTPS channel endpoints. The root must not come from the channel it authorizes.

```sh
python -m aion_lithuanian_market_calendar.update_lifecycle setup --root OWNED_DIR --policy POLICY.json --bootstrap-manifest BOOTSTRAP.json --approved-sha256 VERIFIED_SHA256 --wheelhouse WHEELS --consent
python -m aion_lithuanian_market_calendar.update_lifecycle status --root OWNED_DIR
python -m aion_lithuanian_market_calendar.update_lifecycle notice --root OWNED_DIR
python -m aion_lithuanian_market_calendar.update_lifecycle acknowledge --root OWNED_DIR --notice-version VERSION
python -m aion_lithuanian_market_calendar.update_lifecycle run --root OWNED_DIR -- -c "import sys; print(sys.executable)"
```

Without `--enable-auto-install`, a valid signed offer is recorded for the CLI only. Add `--desktop-notifications` during setup to ask the OS to display an available version. Acknowledging a version suppresses further prompts for it. Headless systems can always read the local notice. Desktop delivery depends on a usable signed-in session and OS notification policy; a successful OS request is not proof that someone saw it.

Alternatively, enroll a **new dedicated root** with `--enable-auto-install`. Only approved compatible patches are installed, verified and promoted; the original interpreter is unchanged. Use `run` or a separately reviewed launcher to select the managed runtime. Controller updates, running application restarts and protected trading workloads require separate authorization. Use `stop`, `disable`, `offline`, `uninstall` or `rollback` with the same `--root`; `start --consent` resumes stopped supervision. Uninstall retains recovery evidence. No change to unrelated environments. The disposable runner exercises signed root/key rotation, monotonic sequences, mandatory revocations and rollback.
