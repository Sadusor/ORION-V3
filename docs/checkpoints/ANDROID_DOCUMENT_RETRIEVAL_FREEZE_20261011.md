# ORION V3 — Android Document Retrieval: Owner-Accepted Freeze

Date: 2026-10-11
Decision: **FROZEN — do not edit accepted working modules without new explicit owner permission.**

## Physically demonstrated
1. Native Android ORION Tools → Document opened the Android document picker.
2. Owner selected `ORION_Document_Retrieval_Test.txt`; Android displayed `Indexed ORION_Document_Retrieval_Test.txt. Ask ORION about it.`
3. Owner selected the **PC Qwen** model and asked: "For NEBULA-742, who is the coordinator and where is the meeting? Cite the uploaded document."
4. PC Qwen answered **Marina Example** and **Blue Observatory Room**, citing `ORION_Document_Retrieval_Test.txt` **page 1, part 0**.
5. A separate earlier question accidentally sent to the phone-local model is not part of the PC retrieval acceptance.

## Accepted source baseline
ORION source commit: `303e5fff4cd62cd63199cf116ea05062b8340b73`.
Earlier GITCHECK: `ORION_DOCUMENT_END_TO_END_SOURCE_GITCHECK> PASS_SOURCE` (24/24 source tests).
Android picker + bridge: `d771eb3bfc43976b0a097461f56941a09da39045`.
UI sheet/toast correction: `303e5fff4cd62cd63199cf116ea05062b8340b73`.
TheHands evidence for corrected Android build: session `57e1a701dc25`, result PASS, `ANDROID_APK_BUILD> PASS`.

## Frozen components and boundaries
- `src/orion_v3/modules/document_index_v1.py`
- `src/orion_v3/modules/document_universal_adapter_v1.py`
- `src/orion_v3/modules/document_chat_connector_v1.py`
- `src/orion_v3/modules/document_intake_v1.py`
- `ui/strata/modules/document-attachment-v1.js`
- Android document-picker hookup in `android/app/src/main/java/com/sadusor/orionv3/MainActivity.kt`
- Android indexed upload code in `android/app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt`
- Android Tools/Document UI hookup in `android/app/src/main/assets/offline/index.html`
- Existing `src/orion_v3/product_server.py` document endpoint and chat integration
- Earlier frozen Gitea source-grounding, canonical memory, authorization, STOP, and History Integrity modules remain frozen.
- **TheHands is a separate frozen product; do not alter its runtime.**

## Qualified scope, limitations
- Owner observed successful end-to-end retrieval for a small TXT document through the PC Qwen model and citation in the answer.
- Import currently supports TXT, MD, CSV, JSON, LOG up to 2 MB; PDF and image ingestion are not part of this acceptance.
- Owner pairing is required for document-index API.
- This acceptance does not establish general factual accuracy on all documents, database imports, or phone-offline-model indexed retrieval.
- Future changes must be new modules/adapters first. Any direct edit to these accepted components requires explicit owner approval for the specific change.

## Next step
Wait for owner's next instruction. Do not independently expand or redesign the accepted path.
