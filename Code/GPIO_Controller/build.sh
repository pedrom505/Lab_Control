#!/bin/bash

echo "Compilando biblioteca GPIO_Control..."

rm GPIO_Control.o
rm GPIO_Control.so

# Verifica se o arquivo objeto existe
echo "Compilando arquivo GPIO_Control.cpp"
g++ -c -fPIC GPIO_Control.cpp -o GPIO_Control.o

echo "Gerando biblioteca GPIO_Control.so"
# Gera a biblioteca compartilhada
g++ -shared -o GPIO_Control.so GPIO_Control.o -lwiringPi

# Verifica se a compilação foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "Biblioteca criada com sucesso: GPIO_Control.so"
else
    echo "Erro ao compilar a biblioteca."
fi