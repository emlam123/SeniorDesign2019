print('reading MCP3008 values, press Ctrl-C to quit...')

#print(('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
#print('-' * 57)

while True:
    values = [0]*8
    for i in range(8):
        values[i] = mcp.read_adc(i)

    print(('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))

    time.sleep(0.5)

