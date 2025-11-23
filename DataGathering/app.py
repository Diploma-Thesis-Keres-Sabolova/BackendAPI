from Utils.YamlReader import YamlProviderLoader
from dotenv import load_dotenv

def main():

    load_dotenv("/app/.env")

    #debbug purposes
    #load_dotenv()

    loader = YamlProviderLoader("/app/DataGathering/providers.yaml")

    #debbug purposes
    #loader = YamlProviderLoader("providers.yaml")

    providers = loader.load_providers()

    for provider in providers:
        try:
            provider.run()
        except Exception as e:
            print(f"❌ Provider {provider.name} failed: {e}")

if __name__ == "__main__":
    main()