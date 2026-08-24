import sys
import subprocess

"""
Пусковой стартовый скрипт, для сборки зависимостей и скачивания необходимых компонентов.
Важно! Перед запуском должно быть создано виртуальное окружение, и название папки должно быть .venv
"""


def start():
    print(f'1.Установка uv')
    cmd = [sys.executable, '-m', 'pip', 'install', 'uv']
    subprocess.run(cmd, shell=False)

    print(f'2.Установка пакетов.')
    cmd = [sys.executable, '-m', 'uv', 'sync']
    subprocess.run(cmd, shell=False)


if __name__ == '__main__':
    start()
