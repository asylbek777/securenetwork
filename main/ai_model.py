import torch
import torch.nn as nn

# Определяем класс нейронной сети
class SimpleBruteForceNN(nn.Module):
    def __init__(self):
        super(SimpleBruteForceNN, self).__init__()
        self.hidden1 = nn.Linear(3, 32)
        self.hidden2 = nn.Linear(32, 16)
        self.hidden3 = nn.Linear(16, 8)
        self.hidden4 = nn.Linear(8, 4)
        self.hidden5 = nn.Linear(4, 2)
        self.output = nn.Linear(2, 1)

    def forward(self, x):
        x = torch.relu(self.hidden1(x))
        x = torch.relu(self.hidden2(x))
        x = torch.relu(self.hidden3(x))
        x = torch.relu(self.hidden4(x))
        x = torch.relu(self.hidden5(x))
        x = torch.sigmoid(self.output(x))
        return x


# Загрузка модели
model_path = "/home/django/PycharmProjects/corporation_network/main/brute_force_model11.pth"

def load_model():
    model = SimpleBruteForceNN()
    model.load_state_dict(torch.load(model_path))
    model.eval()
    return model


# Использование модели для предсказания
def predict_brute_force(data):
    model = load_model()
    input_data = torch.tensor([data], dtype=torch.float32)
    with torch.no_grad():
        prediction = model(input_data)
        return torch.round(prediction).item()
