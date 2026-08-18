# Final Review Fix Report

## Scope and delivery

This remediation addresses all three Important and all three Minor findings in
`final-fix-brief.md` across the two approved linked worktrees only:

- Hub: `D:/20_Dev_Projects/RDK-Skills/rdk-skills/.worktrees/plugin-catalog-remediation`
- Source: `D:/20_Dev_Projects/RDK-Skills/rdk-device-skills/.worktrees/plugin-catalog-remediation`

Signed implementation commits:

- Source `90d5bf9` — `fix: gate workspace router handoffs`
- Hub `95199cf` — `fix: harden plugin catalog routing`

## Findings resolved

| Finding | Resolution |
| --- | --- |
| Workspace-router handoffs were not availability-gated | Added an explicit per-router availability check, exact `rdk-pack-installer` fallback pack, restart, and retry contract to all five affected source Skills; mirrored them byte-for-byte to Hub; added source and Hub contract tests. |
| Registry repository and clone destination were insufficiently constrained | Generator now accepts only a safe exact `owner/repo` slug and rejects empty components, extra segments, whitespace, `..`, backslashes, and shell metacharacters. Installer clones only to `<tmp>/pack` and runs only `<tmp>/pack/<install_script>`. |
| `agent-setup.md` could blur the execution boundary | Installer defines it as optional read-only context that cannot add to or replace the registry-validated install script. Any extra action requires separate confirmation and a target proven inside the confirmed project root. |
| Missing registry `ref` behavior lacked characterization | Added a regression test locking the existing `main` default. The test passed before production changes, so no unnecessary behavior change was made. |
| Finder installation documentation used placeholders instead of the exact public command | README, Chinese README, and usage documentation now contain literal `npx skills add d-robotics/rdk-skills --skill <skill-name>`. |
| Finder accepted `--limit 0` | Parser now rejects values below 1 with `--limit must be at least 1`; a CLI regression test checks nonzero status, empty stdout, and clear stderr. |

## TDD evidence

Hub focused RED run used seven targeted test methods. The existing missing-ref
default test passed immediately; the other new contracts produced the expected
19 subfailures (unsafe repository values, installer clone/boundary behavior,
router availability fallback, exact documentation command, and zero limit).
After implementation, the same seven tests passed, 7/7.

Source RED began with the missing route-check API, then produced two expected
contract failures. Tightening the contract to require the availability check
and fallback in one atomic sentence produced one further expected failure.
After the Skill and validator changes, `python -B -m unittest
tools.test_sandbox -v` passed 3/3.

## Generation and build verification

The catalog generator was run twice consecutively with stable output:

- `skills/rdk-pack-installer/references/pack-registry.json`:
  `BD8DC7F587A5617718B6CC9ECA769DD159174DE2C50C32BB394084FE0F8D0365`
- `skills/rdk-skill-finder/references/skill-index.json`:
  `A6AA9431D50F3ACED4043E3C0F6C68EB7DF16210D9B4C78BB57F91A5F6169218`

The real plugin build completed under WSL using an isolated verified Mike
Farah yq v4.45.4 binary (SHA-256
`B96DE04645707E14A12F52C37E6266832E03C29E95B9B139CDDCaE7314466E69`).
It regenerated the bundled plugin and all four marketplaces. The first attempt
failed before build execution because the WSL PATH used a PowerShell-formatted
working directory; retrying with the absolute WSL path succeeded. The isolated
yq and LF-normalized build-script copy were removed after verification.

## Regression results

| Check | Result |
| --- | --- |
| Hub `python -B -m unittest discover -s tests -v` | 46 passed, 1 skipped. The skip is the Windows process's unavailable-yq dry-run; the same test passed 1/1 under WSL with isolated yq. |
| Hub enforcing strict-L2 validation: `rdk-pack-installer` | 0 L1, 0 L2. |
| Hub enforcing strict-L2 validation: `rdk-skill-finder` | 0 L1, 0 L2. |
| Hub advisory validation | 91 Skills; 137 L1 and 367 L2; advisory exit 0. The accepted pre-fix baseline was 139 L1 and 367 L2. |
| Source focused route contract | 3/3 passed. |
| Source direct route checks | Retired-route problems 0; workspace-router availability problems 0. |
| Source full sandbox | Expected historical exit 1: routing 62/64, 83 structural problems, four Windows/local-doc-search failures; both isolated TROS fixture checks pass. |
| JSON parse sweep | 28/28 JSON files parsed. |
| Diff hygiene | `git diff --check` passed in both repositories before commit. |

The five newly edited routed Skills retain pre-existing strict-L2 failures that
are outside this review scope: each lacks the standard Purpose, When to use,
Instructions, and Safety sections; `rdk-hardware` additionally retains its
existing missing `scripts/board_probe.sh` cross-reference. Each has 0 L1
errors. No baseline was worsened.

## Byte-identical source/Hub mirrors

All 14 approved source/Hub pairs match:

| File | SHA-256 |
| --- | --- |
| `rdk-accessories/SKILL.md` | `05FA54C3F200A654895C1370EEF2F2CE6037FB0CED8C30AC79A1350CAAF04799` |
| `rdk-board-delegate/SKILL.md` | `09F4BA63097D4AF3C17A71670FD367CC5759B39CF7A5671D9D62E3B36C051AED` |
| `rdk-board-knowledge/SKILL.md` | `143BE300D1135D7A247C7047FF0A9DF8672E3B74ACF331992BCD814478A25E05` |
| `rdk-command-manual/SKILL.md` | `7BB783F5C0256B45C0B5A0FB6118D0BF381CCFAB8BE5D9F7FF91F0368A695A8C` |
| `rdk-ecosystem/SKILL.md` | `98DE167191D3D19F1010B56CB92136D91BE8041ADF3857FD58D92097F0018E59` |
| `rdk-embodied-lerobot/SKILL.md` | `8CDBC70D94D919A5862D9C048D80B15F5D5EB546213E435BA28B444F4865A075` |
| `rdk-hardware/SKILL.md` | `B370138F016C6FBEC2DCC921AD44E85B0B9EE40F88F7FA5E823E1A48032B610D` |
| `rdk-llm-deployment/SKILL.md` | `814C87177626791806B4FC062E554DA90F0D0E25538DCB4126149DD9C8539081` |
| `rdk-log-forensics/SKILL.md` | `3FFEB79E6C98F00FC62E910846BCF3BD571DB551E1CAED1AA23D6CE3C9C48027` |
| `rdk-model-zoo/SKILL.md` | `4092F6774F7BE8EC8E8DDF19661AE8BB5C68AB41EB0AAC8FBB3A4D3416191C9D` |
| `rdk-multimedia/SKILL.md` | `A5C3DC398112DF7330F1C9CCA373F0BB9D7A8B7D4694485BE05F1FB530B80BBB` |
| `rdk-source-map/SKILL.md` | `80EAF2C7BCA708C80272DEB34533145642BBFD8640259AD976FDED07CC289D14` |
| `rdk-docs-reference/SKILL.md` | `EA085FC8A7D7361819238663DE846C75D6FD15605182901437BF6B84A03E3122` |
| `rdk-docs-reference/scripts/search_docs.sh` | `B1BC32C6A254AC6F00753CB4E50259756445433E3B801006DB2716E7ED705E9C` |

All 14 canonical/bundled-plugin file pairs also match byte-for-byte. Temporary
test caches and build/tool directories were removed before delivery.
