from models.subtitle import Subtitle

if __name__ == '__main__':

    subtitle = Subtitle('data/sub_kurz.srt')
    subtitle.parse_file()
    #print(subtitle)
    block0 = subtitle.blocks[0]

    print()
    print(block0)
    print()
    block0.add_line('abc')
    print()
    print(block0)
    print()
    subtitle.undo()
    print(block0)

    '''
    block0.id = 10
    block0._text = ['some text', 'another line']
    print(block0, '\n  ', block0.mementos, '\n')

    block0.reset()
    print(block0, '\n  ', block0.mementos, '\n')
    '''

    '''
    block = Block(10)
    subtitle.insert_block(block)
    print(subtitle.validate())

    print(subtitle)
    print("=====")
    '''