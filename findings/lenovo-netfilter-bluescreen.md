---
topic: lenovo-netfilter-bluescreen
area: Software process
question: Is there a known fix for a Windows blue screen that names FBNetFlt.sys on a Lenovo gaming laptop? (Separate entry - a driver fault, not heat or a GPU driver update.)
checked: 2026-11-28
review_months: 6
status: current
---
# Blue screen naming FBNetFlt.sys on Lenovo laptops

- **Question:** Is there a known fix for a `0xD1` (DRIVER_IRQL_NOT_LESS_OR_EQUAL) blue screen that names `FBNetFlt.sys`?
- **Checked:** 2026-11-28
- **Evidence strength:** *anecdotal* (one community answer read; guides and forum posts seen as search summaries). No vendor statement.

## Finding

- `FBNetFlt.sys` is a Lenovo network filter driver behind the "Network Boost" feature; a Microsoft Q&A answer to the same `0xD1` crash says to check that Network Boost is disabled (standard: [Microsoft Q&A, 2022-05-21](https://learn.microsoft.com/en-us/answers/questions/4339479/bsod-av-fbnetflt-unknown-function-help), community answer, no vendor role shown).
- Guides say Lenovo Vantage or Nerve Center installs it, and suggest uninstalling the "Lenovo Gaming NetFilter Device" in Device Manager (hidden devices shown) or removing those apps if disabling is not enough; they advise against deleting the file by hand (standard: [TheWindowsClub](https://www.thewindowsclub.com/fix-fbnetflt-sys-blue-screen), [Lenovo community thread](https://forums.lenovo.com/t5/Gaming-Laptops/lenovo-legion-y530-blue-screen-stop-code-DRIVER-NOT-LESS-OR-EQUAL-what-failed-FBnetFLT-sys/m-p/4412149); search summaries only, the pages did not load).
- **Open:** no fixed driver version and no official Lenovo fix was found.

## Limits

The Lenovo downloads page refused the fetch and the forum thread returned no body. A newer driver may exist on the model's support page; check there.
