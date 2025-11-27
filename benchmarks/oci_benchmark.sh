export HF_TOKEN="<your_huggingface_token_here>"
export COMPARTMENTID="ocid1.compartment.oc1..aaaaaaaaxxxxxxxxxy"
export ENDPOINTID="ocid1.generativeaiendpoint.oc1..aaaaaaaaxxxxxxxxxy"
export REGION="sa-saopaulo-1"
export API_MODEL_NAME="meta.llama-4-maverick-17b-128e-instruct-fp8"
export MODEL_TOKENIZER="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

/home/opc/.venv/bin/genai-bench benchmark --api-backend oci-genai \
            --auth "instance_principal" \
            --api-base "https://inference.generativeai.$REGION.oci.oraclecloud.com" \
            --api-model-name "$API_MODEL_NAME" \
            --model-tokenizer "$MODEL_TOKENIZER" \
            --task text-to-text \
            --max-time-per-run 10 \
            --max-requests-per-run 64 \
            --traffic-scenario "N(5000,0)/(25,0)" \
            --num-concurrency 1 \
            --num-concurrency 2 \
            --num-concurrency 4 \
            --num-concurrency 8 \
            --num-concurrency 16 \
            --num-concurrency 32 \
            --num-concurrency 64 \
            --additional-request-params '{"compartmentId": "'"$COMPARTMENTID"'", "endpointId": "'"$ENDPOINTID"'", "servingType": "DEDICATED"}' \