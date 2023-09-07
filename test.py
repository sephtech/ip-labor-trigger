import select
import socket
import queue

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)
server.bind(('0.0.0.0', 50000))
server.listen(5)
inputs = [server]
outputs = []
in_queues = {}
out_queues = {}

while inputs:
    try:
        readable, writable, exceptional = select.select(
            inputs, outputs, inputs)
        for s in readable:
            if s is server:
                connection, client_address = s.accept()
                connection.setblocking(0)
                inputs.append(connection)
                in_queues[connection] = queue.Queue()
                out_queues[connection] = queue.Queue()
            else:
                data = s.recv(1024)
                if data:
                    in_queues[s].put(data)
                    if s not in outputs:
                        outputs.append(s)
                else:
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    del in_queues[s]

        for s in writable:
            try:
                next_msg = out_queues[s].get_nowait()
            except queue.Empty:
                outputs.remove(s)
            else:
                s.send(next_msg)

        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del in_queues[s]
    except KeyboardInterrupt:
        break
    for key, q in in_queues.items():
        try:
            msg = q.get_nowait()
            print(msg)
            out_queues[key].put(msg + b'1')
        except queue.Empty:
            pass
