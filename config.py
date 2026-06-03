from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_url: str = "sqlite:///./pipeline.db"
    redis_url: str = "redis://localhost:6379/0"
    vast_api_key: str = "f5d5bc367728ff9297d6edee968a345cb66d25e8ca2299a82d816a6ee5d54ae5"
    environment: str = "production"  # "development" (RTX 3090 testing) or "production" (RTX 4090 production)
    vast_image: str = "hearmeman/comfyui-wan-template:v11"
    vast_onstart_script: str = "chown -v -R root:root /root && chmod -v 700 /root && mkdir -p /root/.ssh && chmod -v 700 /root/.ssh && touch /root/.ssh/authorized_keys && chmod -v 600 /root/.ssh/authorized_keys"
    hf_token: str = ""
    civitai_token: str = ""

    # Dynamic GPU Settings
    dev_gpu: str = "RTX_3090"
    dev_max_price: float = 1.50

    prod_gpu: str = "RTX_4090"
    prod_max_price: float = 2.20
    
    ultra_gpu: str = "H100"
    ultra_max_price: float = 5.00
    
    # Thresholds for queue
    vast_gpu_hour_threshold: int = 5 # arbitrary number of jobs to equal a 'full load' for now
    
    class Config:
        env_file = ".env"

settings = Settings()
