gcloud functions deploy onValidSample \
  --entry-point onValidSample \
  --runtime python39 \
  --trigger-event "providers/cloud.firestore/eventTypes/document.update" \
  --trigger-resource "projects/heartfelt-0/databases/(default)/documents/heartfelt_data/{sample}" \
  --memory=512MB