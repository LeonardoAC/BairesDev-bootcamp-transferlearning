# -*- coding: utf-8 -*-
"""DIO-BairesDev-Transfer learning.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/11RWnmbXBzZ3WSkkCwtPon0a-Jwva3cx_
"""

# Monta o drive do google para receber as imagens armazenadas lá.
# Vai pedir autenticação.
#from google.colab import drive
#drive.mount('/content/drive/')

# -------------------------------------------------------------------------------------
# Exibe algumas subpastas (cat, dog) para termos certeza que está lendo certo.
#import os
#
#image_directory = "/content/drive/MyDrive/Colab_Notebooks/Assets/PetImages/"
#print("Verificando arquivos na pasta...")
#print(os.listdir(image_directory)[:10])  # Mostrar os primeiros 10 arquivos

# -------------------------------------------------------------------------------------
# Exibe alguma imagem para certificar-se que está funcionando
#import cv2
#import matplotlib.pyplot as plt

# Teste com uma imagem real do diretório
#image_path = "/content/drive/MyDrive/Colab_Notebooks/Assets/PetImages/Cat/1.jpg"  # Substitua por um nome válido

# Carregar a imagem
#image = cv2.imread(image_path)  # OpenCV lê em formato BGR
#if image is None:
#    print("Erro ao carregar a imagem! Verifique o caminho.")
#else:
#    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Converter para RGB
#    plt.imshow(image)
#    plt.axis("off")
#    plt.show()

#print("Miauuuuu...!")

# -------------------------------------------------------------------------
# Testar a leitura do Tensorflow

#import tensorflow as tf

# Testar carregamento de imagem com TensorFlow
#image = tf.io.read_file(image_path)  # Ler o arquivo
#image = tf.image.decode_jpeg(image, channels=3)  # Decodificar
#image = tf.image.resize(image, (160, 160))  # Ajustar tamanho

#plt.imshow(image.numpy().astype("uint8"))
#plt.axis("off")
#plt.show()

#print("Se viu um gato novamente, o TF leu a imagem corretamente")

# Pega path onde estou
!pwd
!ls '/content/drive/'

# Descompacta os arquivos baixados em:
# https://www.microsoft.com/en-us/download/details.aspx?id=54765
import zipfile
import os

# Caminho para o arquivo ZIP hospedado no Colab
zip_file_path = '/content/drive/MyDrive/Colab_Notebooks/kagglecatsanddogs_5340.zip'

# Diretório onde você quer extrair os arquivos
extraction_path = '/content/drive/MyDrive/Colab_Notebooks/Assets/'

# Verificar se o arquivo zip existe
if os.path.exists(zip_file_path):
    # Criar o diretório de destino, se não existir
    os.makedirs(extraction_path, exist_ok=True)

    # Descompactar o arquivo ZIP
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extraction_path)  # Extrair para o diretório '/content/drive/MyDrive/Colab Notebooks/Assets/'

    print("Arquivos descompactados com sucesso!")
else:
    print("Arquivo ZIP não encontrado.")

# Passo 1: Obter a Base de Imagens
#
import tensorflow as tf

# Diretório onde as imagens foram descompactadas
image_directory = '/content/drive/MyDrive/Colab_Notebooks/Assets/PetImages/'

# Carregar as imagens diretamente do diretório
train_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    image_directory,
    image_size=(160, 160),  # Ajuste o tamanho das imagens conforme necessário
    batch_size=32,          # Tamanho do lote
    validation_split=0.2,   # Usar 20% para validação
    subset="training",      # Subconjunto de treinamento
    seed=123,               # Semente para reprodutibilidade
)

val_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    image_directory,
    image_size=(160, 160),  # Ajuste o tamanho das imagens conforme necessário
    batch_size=32,          # Tamanho do lote
    validation_split=0.2,   # Usar 20% para validação
    subset="validation",    # Subconjunto de validação
    seed=123,               # Semente para reprodutibilidade
)

# Verificar o sucesso
print(f"Train Dataset: {train_dataset}")
print(f"Validation Dataset: {val_dataset}")

# Passo 2: Preparar os Dados
#

import tensorflow as tf
import tensorflow_datasets as tfds

# Carregar dataset "cats_vs_dogs"
dataset_dict, info = tfds.load("cats_vs_dogs", as_supervised=True, with_info=True)

# Pegar apenas os dados da chave 'train'
dataset = dataset_dict['train']

# Função para normalizar e redimensionar imagens
def format_image(image, label):
    image = tf.image.resize(image, (160, 160))  # Ajusta tamanho
    image = image / 255.0  # Normaliza os valores (0 a 1)
    return image, label

# Aplicar a função de formatação
dataset = dataset.map(format_image)

# Separar em treino e validação
SPLIT_RATIO = 0.8  # 80% treino, 20% validação
total_examples = info.splits['train'].num_examples
train_size = int(SPLIT_RATIO * total_examples)

train_dataset = dataset.take(train_size)
val_dataset = dataset.skip(train_size)

# Criar batches
BATCH_SIZE = 32
train_dataset = train_dataset.shuffle(1000).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
val_dataset = val_dataset.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

print("Dataset preparado com sucesso!")

# Passo 3: Carregar Modelo Pré-Treinado
#

# Carregar MobileNetV2 sem a última camada (para Transfer Learning)
base_model = tf.keras.applications.MobileNetV2(input_shape=(160, 160, 3),
                                               include_top=False,
                                               weights='imagenet')

# Congelar camadas do modelo base
base_model.trainable = False

# Criar nova camada de saída
global_average_layer = tf.keras.layers.GlobalAveragePooling2D()
output_layer = tf.keras.layers.Dense(1, activation='sigmoid')  # 1 nó (cães vs gatos)

# Construir o modelo final
model = tf.keras.Sequential([
    base_model,
    global_average_layer,
    output_layer
])

# Compilar o modelo
model.compile(optimizer=tf.keras.optimizers.Adam(),
              loss='binary_crossentropy',
              metrics=['accuracy'])

model.summary()

# Passo 4: Treinar o Modelo
#

# Separar dados de treino e validação
BATCH_SIZE = 32
SHUFFLE_BUFFER_SIZE = 100

train_dataset = dataset.take(500).shuffle(SHUFFLE_BUFFER_SIZE).batch(BATCH_SIZE)
val_dataset = dataset.skip(100).batch(BATCH_SIZE)

# Treinamento
history = model.fit(train_dataset, validation_data=val_dataset, epochs=5)

print("Treino finalizado!")

# Passo 5: Testar o Modelo
#
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

def predict_image(image):
    """Redimensiona, normaliza e faz a predição da imagem."""
    image = tf.image.resize(image, (160, 160)) / 255.0  # Ajuste do tamanho e normalização
    image = np.expand_dims(image, axis=0)  # Adiciona dimensão batch
    prediction = model.predict(image)[0][0]  # Obtém o valor de saída
    return "Cachorro" if prediction > 0.5 else "Gato"

# 🔹 Pegando uma amostra do conjunto de validação
for images, labels in val_dataset.take(1):  # Pegando um lote (batch)
    image = images[0].numpy().astype("uint8")  # Pegamos apenas a primeira imagem do lote
    plt.imshow(image)  # Exibe a imagem
    plt.axis("off")  # Remove eixos para melhor visualização
    plt.title(f"Predição: {predict_image(images[0])}")  # Predição do modelo
    plt.show()

# Mostrar Algumas Amostras do Dataset
#

import matplotlib.pyplot as plt

# Pegar 100 imagens do dataset de treino
num_samples = 100  # Número de imagens a exibir
samples = list(train_dataset.unbatch().take(num_samples))  # Pega 100 imagens do dataset

# Criar figura
plt.figure(figsize=(10, 10))

# Exibir as amostras
for i, (image, label) in enumerate(samples):
    plt.subplot(10, 10, i + 1)  # Grid 10x10 para exibir 100 imagens
    plt.imshow(image.numpy().astype("uint8"))  # Converter para formato exibível
    plt.title("Gato" if label.numpy() == 0 else "Cachorro")  # Nome da classe
    plt.axis("off")

plt.tight_layout()  # Para ajustar o layout das imagens
plt.show()