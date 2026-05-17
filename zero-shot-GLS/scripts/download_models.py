"""
Download the models and tokenizers from HuggingFace.
"""
import os
import os.path as osp
from transformers import GPTQConfig

os.environ["HF_HOME"] = f"{osp.dirname(__file__)}/../tmp_saves/hg_cache"

from transformers import AutoModelForCausalLM, AutoTokenizer

if __name__ == "__main__":
    # # GPT2
    # model_name = "gpt2-medium"
    # print(f"Downloading {model_name}")
    # AutoTokenizer.from_pretrained(model_name)
    # AutoModelForCausalLM.from_pretrained(
    #     model_name,
    #     max_memory={"cpu": "64GiB"},
    # )

    #Distill
    model_name = "distilgpt2"
    print(f"Downloading {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    # LlaMa2
    # model_name = "TheBloke/Llama-2-7B-chat-GPTQ"
    # print(f"Downloading {model_name}")
    # AutoTokenizer.from_pretrained(model_name)
    #
    # AutoModelForCausalLM.from_pretrained(
    #     model_name,
    #     quantization_config=GPTQConfig(bits=4, disable_exllama=True),
    #     trust_remote_code=False,
    #     revision="main",
    #     max_memory={"cpu": "64GiB"},
    # )
