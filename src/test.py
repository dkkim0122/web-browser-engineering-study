import tkinter.font


window = tkinter.Tk()

canvas = tkinter.Canvas(
            window,
            width=800,
            height=600
        )
canvas.pack()

font1 = tkinter.font.Font(family="Times", size=16)
font2 = tkinter.font.Font(family="Times", size=16, slant="italic")

x, y = 200, 200
canvas.create_text(x, y, text="Hello, ", font=font1, anchor="nw")
x += font1.measure("Hello, ")
canvas.create_text(x, y, text="overlapping!", font=font2, anchor="nw")

window.mainloop()