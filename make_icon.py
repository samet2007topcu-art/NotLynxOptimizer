from PIL import Image, ImageDraw

# 256x256 siber karanlık arka planlı simge tuvali
img = Image.new("RGBA", (256, 256), (5, 7, 10, 255))
draw = ImageDraw.Draw(img)

# Siber vaşak hatları ve çerçeve
draw.polygon([(128, 20), (236, 80), (200, 200), (128, 236), (56, 200), (20, 80)], outline=(0, 255, 102, 255), width=10)
# Neon parlayan gözler
draw.polygon([(90, 110), (120, 110), (105, 135)], fill=(0, 255, 102, 255))
draw.polygon([(166, 110), (136, 110), (151, 135)], fill=(0, 255, 102, 255))

img.save("app.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
print("app.ico başarıyla oluşturuldu!")