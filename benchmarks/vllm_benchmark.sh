export HF_TOKEN="<your_huggingface_token>"
export API_BASE="<your_api_base_url>"

genai-bench benchmark --api-backend openai \
            --api-base "$API_BASE" \
            --api-key "<password>" \
            --api-model-name "meta-llama/Llama-3.3-70B-Instruct" \
            --model-tokenizer "meta-llama/Llama-3.3-70B-Instruct" \
            --task text-to-text \
            --max-time-per-run 10 \
            --max-requests-per-run 1536 \
            --traffic-scenario "N(480,240)/(300,150)" \
            --traffic-scenario "N(2200,200)/(200,20)" \
            --num-concurrency 1 \
            --num-concurrency 2 \
            --num-concurrency 4 \
            --num-concurrency 8 \
            --num-concurrency 16 \
            --num-concurrency 32 \
            --num-concurrency 64 \
            --num-concurrency 128 \
            --num-concurrency 256 \
            --server-engine "vLLM" \
            --server-gpu-type "H100" \
            --server-version "0.10.2" \
            --server-gpu-count 8
