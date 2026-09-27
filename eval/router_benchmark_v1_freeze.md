# Router Benchmark V1 — Freeze Record

- **Status:** `frozen`
- **Frozen date:** 2026-09-27 (Asia/Shanghai)
- **Corpus:** `github/site-policy`, 57 policy documents under `data/site-policy/Policies`
- **Corpus commit:** `b9578b546d2506febda1da2cd7431644d58e512c`
- **Original author:** Sol (`benchmark_author`)
- **Independent auditor:** DeepSeek
- **Audit dispositions:** 17 KEEP / 3 RECLASSIFY / 0 EDIT / 0 REMOVE
- **Freeze gate:** `PASS_WITH_NOTE`; see `eval/router_benchmark_v1_freeze_gate.md` for measured surface bias.
- **Query integrity:** all 20 query strings are unchanged from the original draft.
- **Routing gold:** none. No DIRECT / DECOMPOSE label, oracle decision, or expected winner is included.

## Frozen queries (20)

- **router_001:** Someone copied my home address from a public website into a GitHub issue and urged others to contact me. Can I report this as a privacy violation, and is the private-information removal request the right way to get it taken down?
- **router_002:** A repository contains no intimate images, but it advertises a tool for making realistic sexual images of real people without their consent. Does hosting only the tool put the project outside GitHub's policy?
- **router_003:** A contributor keeps opening empty pull requests and new accounts after I block them, flooding reviewers with notifications. Which GitHub conduct rules apply, and can staff act beyond moderation of my repository?
- **router_004:** Our museum repository explains the history of nude artwork, but its account avatar previews one of the images. Does the educational context mean GitHub must leave both the repository and avatar visible to everyone?
- **router_005:** I'm posting a satirical graphic about a medical claim. Its README labels it as satire and links to sources, but the image could circulate without that context. How does GitHub assess whether it crosses the misinformation policy?
- **router_006:** We published an exploit demo for defensive research, and an active malware campaign now links to its download. Could GitHub limit that release without banning every copy, and how could we challenge a restriction we think is mistaken?
- **router_007:** An account uses our registered company name as its handle, copies our logo, and calls itself parody. Is the matching name enough to reclaim the handle, or what would GitHub look at?
- **router_008:** Our README, package description, and profile mention another company's product to explain compatibility, without claiming affiliation. When would that use become a GitHub trademark-policy problem?
- **router_009:** I found a vulnerability in GitHub and reporting it may involve conduct normally restricted by its site policies. Does the bug bounty safe harbor cover that research, and does it let me test a connected third-party service?
- **router_010:** A DMCA notice identifies one file in my repository and one part of a published package. Can I edit both before GitHub disables anything, and what must I tell GitHub after making changes?
- **router_011:** A repository exposes our internal network diagram and republishes our copyrighted manual. Should I put both into one private-information removal request, and what would GitHub need to assess each?
- **router_012:** I found a notice naming my project in GitHub's public government-takedowns repository. Does that mean GitHub decided my project was unlawful, and what does the listing actually tell readers?
- **router_013:** A government office says my public repository is illegal locally and also wants private data from my account. Does its content-takedown request give it that data, and how are the two requests handled?
- **router_014:** Police say they need my private repository immediately to prevent serious harm. Could GitHub disclose its contents under the emergency exception without a warrant, and would I be told first?
- **router_015:** I use a personal account and keep code in a private repository, but paste a snippet into a GitHub AI feature. Does “private” prevent GitHub from using that input to improve AI, and what changes if I opt out?
- **router_016:** Our paid Marketplace app was disabled for a policy reason halfway through its annual term. Who should notify us, does payment guarantee continued access, and are we owed a partial refund?
- **router_017:** I want to thank Sponsors by displaying their logos in my README and Sponsor content, then promote their products in other users' issue threads. Where does GitHub draw the line on that kind of promotion?
- **router_018:** At a GitHub event, staff are filming the room while another attendee records me after I say no. Do the same consent rules apply to both, and how can I report the attendee's conduct?
- **router_019:** I normally live outside a trade-restricted region, but my account was flagged while I was traveling through one. Have I permanently lost access to my private repositories, and what can I do if the flag is mistaken?
- **router_020:** Our enterprise admin sees a vendor on GitHub's subprocessor list and has also installed a Marketplace app. Are both covered by the same GitHub data-processing commitments, and who is responsible for the app's access to our data?

## Freeze rule

These 20 query strings must not be modified in response to later Router runs or results. The approved metadata reclassifications are recorded in `eval/router_benchmark_v1_audit_changes.json`; the original draft files remain preserved.

The source-layout groups and benchmark properties describe intended evidence structure. They are not routing decisions. Single-document cases may still require evidence from separate sections.

- **Frozen JSON SHA-256:** `a345ccfd8dabadedd41ac1abc341a079709d3bbc699e4ea7b3696a06f76acf16`
- **Freeze candidate JSON SHA-256:** `75277537d4ef6aeeb1eee33c9f0ab160afb2c49204ec7605021e606b5b5db0f9`
