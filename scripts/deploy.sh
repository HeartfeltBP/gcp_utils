gcloud functions deploy onNewFrame \
  --entry-point onNewFrame \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/frames/{frame}" \
  --memory=512MB &

gcloud functions deploy onNewWindow \
  --entry-point onNewWindow \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/windows/{window}" \
  --memory=512MB &

gcloud functions deploy onValidWindow \
  --entry-point onValidWindow \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.update" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/bpm_data/{uid}/windows/{window}" \
  --memory=512MB &