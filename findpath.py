import ttkbootstrap
import os

# Pega o caminho de onde a biblioteca ttkbootstrap está instalada
lib_path = os.path.dirname(ttkbootstrap.__file__)

# Monta o caminho completo para a pasta de temas
themes_path = os.path.join(lib_path, "themes")

print("\n" + "="*50)
print("COPIE O CAMINHO ABAIXO PARA USAR NO auto-py-to-exe:")
print(themes_path)
print("="*50 + "\n")