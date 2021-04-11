import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import time
import pygame

pygame.mixer.init()
start = time.perf_counter()
pygame.mixer.music.load("./mario/smb_1-up.wav")
call_time = time.perf_counter() - start

print("load: ", call_time)

start = time.perf_counter()
pygame.mixer.music.play()
call_time = time.perf_counter() - start
print(call_time)
while pygame.mixer.music.get_busy() == True:
    continue

effect = pygame.mixer.Sound("./red-alert/good-to-go.mp3")
effect2 = pygame.mixer.Sound("./red-alert/i-go-freely.mp3")
start = time.perf_counter()
channel = effect.play()
call_time = time.perf_counter() - start
print(call_time)

while channel.get_busy():
    pygame.time.wait(100)  # ms
    print("Playing...")
start = time.perf_counter()
effect2.play()
call_time = time.perf_counter() - start
print(call_time)
while True:
    pass
