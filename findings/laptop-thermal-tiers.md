# Laptop temperature tiers for long unattended jobs

- **Question:** Which GPU temperatures are normal, worth flagging or dangerous on a laptop running long jobs, and what wears the laptop out over time?
- **Checked:** 2026-11-14
- **Evidence strength:** *anecdotal* for what the nvidia-smi temperature fields mean (NVIDIA developer forum replies; NVIDIA's own manual was not found); *vendor or single source* for battery care (Lenovo user guide, Battery University); *common practice* for the Arrhenius rule of thumb, with its sources disputing how far it applies.

## Finding

- **Read the card's own limits; don't use a generic number.** `nvidia-smi -q -d TEMPERATURE` lists them. Forum replies on NVIDIA's developer forum say: *Target Temperature* is the set point the fan control aims to hold; *Slowdown Temp* is where the clocks throttle; *Shutdown Temp* is where the GPU turns off. What *Max Operating Temp* means is disputed. Notebook GPUs often have a fixed target that can't be changed. One guide adds: when the laptop maker publishes a lower limit than the GPU vendor, use the lower one.
- **Tiers (checker's synthesis from the above, not a published scale):** below Target = normal; at or near Target for long stretches = working as designed, but the fan is at its limit; any thermal-slowdown time (`clocks_event_reasons` thermal bits, or a non-zero `SW/HW Thermal Slowdown` counter) or a reading at Slowdown Temp = throttling, which costs speed and makes timing runs unreliable; Shutdown Temp = protection trip. Generic guides put the usual laptop GPU throttle point around 90 °C, and say under 85 °C is safe for desktop cards. These are secondary sources.
- **Long-term wear from heat is real but not quantified for GPUs.** The "every 10 °C halves lifetime" rule comes from the Arrhenius equation. It fits some failure mechanisms (electromigration, corrosion), with an activation-energy-dependent factor of about 2 per 10 °C over roughly 75-125 °C, and not others. Electronics Cooling and TI both call it a rule of thumb. TI's industrial parts are rated for 10 years at 105 °C junction. No GPU-specific wear data was found. Checker's inference: running cooler extends life by an unknown amount, and a running record of temperature is what lets a trend (dust, dried paste) show up.
- **The battery is the part heat wears out fastest.** Heat combined with a full charge oxidises the cells irreversibly (Battery University; a 2024 RSC Advances study on cells stored fully charged at 45 °C). Battery University says a laptop's interior reaches about 45 °C in use, and that life expectancy at high temperature is half that at 20 °C. Lenovo recommends conservation mode for a laptop that stays plugged in; it caps the charge (75-80% on some Legion models per Lenovo's guide, about 55-60% on others per Lenovo support and user reports). It is switched in Lenovo Vantage, PC Manager or Legion Zone.

## Sources

- [NVIDIA forum: target temperature and max operating temperature](https://forums.developer.nvidia.com/t/nvidia-smi-gpu-target-temperature-maximum-operating-temperature/229325) (vendor forum, replies not official docs).
- [NVIDIA forum: Max Operating Temp seems low for laptop 3060](https://forums.developer.nvidia.com/t/gpu-max-operating-temp-seems-low-for-laptop-3060/262268) (vendor forum).
- [Electronics Cooling: does a 10 °C rise really halve the life of electronics?](https://www.electronics-cooling.com/2017/08/10c-increase-temperature-really-reduce-life-electronics-half/) (trade journal).
- [TI: effect of temperature on electromigration (SPRABX4)](https://www.ti.com/document-viewer/lit/html/SPRABX4B/effect-of-temperature-on-electro-migration-sprabx44304) (vendor application note).
- [Battery University: portable computing](https://www.batteryuniversity.com/article/portable-computing/) (vendor-run reference site).
- [RSC Advances 2024: LiCoO2/graphite cells stored fully charged at high temperature](https://pubs.rsc.org/en/content/articlepdf/2024/ra/d3ra07938d) (peer-reviewed).
- [Lenovo Legion Pro 7 user guide: battery care](https://download.lenovo.com/pccbbs/pubs/legion_pro7_16/user_guide/en/help_stay_energetic.html) (official docs).
- [Lenovo support: battery stops at 60%](https://support.lenovo.com/hn/en/solutions/ht103159) (official support page, ideapad).
- [Corsair: how hot is too hot for a GPU](https://www.corsair.com/it/cs/explorer/diy-builder/fans/how-hot-is-too-hot-for-a-gpu/) (vendor blog, desktop figures).

## Limits

NVIDIA's nvidia-smi manual was not read, so the field meanings rest on forum replies. No source gives a laptop GPU's lifetime as a function of temperature. Battery figures come from cells and general guides, not from measurements on a specific laptop model. CPU limits are in `findings/laptop-cpu-thermal-limit`.
