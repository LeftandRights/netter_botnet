import typing, os

if typing.TYPE_CHECKING:
    from ..handler import ServerHandler

def run(socketInstance: 'ServerHandler', filename: str, textIO: typing.TextIO) -> None:
    tk = __import__('tkinter')
    root = tk.Tk()

    root.geometry("720x480")
    root.title('Text Editor')

    TextInput = tk.Text(root, height = 25, width = 80)

    FileTitle = tk.Label(root, text = filename)
    FileTitle.config(font = ("Courier", 14))

    FileTitle.pack()
    TextInput.pack()

    # ================================================================ #

    def download_file() -> None:
        socketInstance.socketInstance.send_packet('download ' + textIO.read())
        root.destroy()

    def delete_file() -> None:
        textIO.close(); os.remove(filename)
        socketInstance.socketInstance.send_packet('File deleted.')
        root.destroy()

    def save_file() -> None:
        socketInstance.socketInstance.send_packet('File saved.')
        open(filename, 'w').write(TextInput.get("1.0", "end-1c"))
        root.destroy()

    saveFile_button = tk.Button(root, text = 'Save File', command = save_file, width = 20)
    saveFile_button.place(x = 295, y = 440)

    deleteFile_button = tk.Button(root, text = 'Delete File', command = delete_file, width = 20)
    deleteFile_button.place(x = 500, y = 440)

    downloadFile_button = tk.Button(root, text = 'Download File', command = download_file, width = 20)
    downloadFile_button.place(x = 90, y = 440)

    TextInput.insert(tk.END, textIO.read())
    tk.mainloop()
