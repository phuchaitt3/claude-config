# Laptop CPU at 95-100 °C under load

- **Question:** Is a laptop CPU that swings between 70 and 100 °C under sustained load overheating, or working as designed?
- **Checked:** 2026-11-13
- **Evidence strength:** *official standard* for the temperature limit (Intel figures, cited by Dell); *anecdotal* for how laptop makers tune it.

## Finding

- Intel laptop CPUs have a maximum junction temperature (Tj max): 100 °C for Raptor Lake and 110 °C for Meteor Lake, per Intel figures cited by Dell support. At that limit the CPU lowers its power and clock speed (thermal throttling) to protect itself. Reaching it under heavy load is within the design, not damage.
- Some makers set the throttle point lower (one forum claim: 95 °C on a Lenovo), and the same CPU settles at very different temperatures in different chassis (Notebookcheck: 82 °C in two gaming laptops, over 100 °C in another, under the same load).
- Hitting the limit often or for long periods costs speed. The usual fixes are less load, better airflow (a stand, clean vents), the maker's quieter power mode, or a repaste. Checker's inference: on a laptop shared by agent chats the lever is how many heavy jobs run at once, which belongs with `findings/shared-gpu-one-machine` and `findings/agent-process-and-resource-control`.

## Sources

- [Dell: Alienware laptop CPU performance behaviour](https://www.dell.com/support/kbdoc/en-in/000214549/alienware-x14-r2-and-x16-r1-cpu-performance-behavior) (official support page; Intel Tj max figures).
- [LaptopWiki thermal guide](https://laptopwiki.eu/laptopwiki/guides/general/thermalguide) (community guide).
- [Notebookcheck: CPUs over 100 °C under load](https://www.notebookcheck.net/Core-Ultra-9-290HX-Plus-is-one-of-the-warmest-mobile-CPUs-at-over-100-C-under-load.1279328.0.html) (tech press).
- [TechPowerUp forum thread on PROCHOT](https://techpowerup.com/forums/goto/post?id=5384669) (forum).

## Limits

No Lenovo document was found for the exact model's limit; check the CPU's own spec sheet. The sources measure games and stress tests, not containers or model inference. No source found covers long-term wear from running at the limit; `findings/laptop-thermal-tiers` (2026-11-14) has the general rule of thumb, GPU tiers and battery wear.
