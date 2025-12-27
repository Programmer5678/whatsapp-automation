import qrcode

data = "2@eSPBvDjFHwxq3wC90KF0Bt84usZ3bUf58NDKYEUCfCzxwjKzVM6g3dF4u8+/KuTkR6Hns383E4wW5+5WTRYleWe0V7ex+QdYkO0=,hfgUcejLP38R8V3V/T16sq9gGSS7bjfNUqhJhRt9S0k=,aTP4Oa1h41e1xKhmEDeHcBRT0yQrvfo2xcyAJM+rwRw=,WLF6n5fmJpPeOL7gVNqeXZuuaQuYKb30o/vpujeuuJI="
img = qrcode.make(data)
img.save("output.png")

print("Image saved as output.png")