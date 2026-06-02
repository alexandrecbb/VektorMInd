from dotenv import load_dotenv
load_dotenv()
from puppy import LLMAgent
if __name__ == '__main__':
    agent = LLMAgent.load_checkpoint("data/05_train_model_output/agent_1")
    df = agent.portfolio.get_action_df()
    df.write_csv("petr4_gemini_actions.csv")
    print("Resultados salvos em petr4_gemini_actions.csv")