from tetris_plugin import Tetris, MyOnLeft, MyOnRight, MyOnDown, MyOnUp, MyOnDrop, MyOnCw, MyOnCcw, MyOnNewBlock, MyOnFinished, TetrisState
from matrix import Matrix

BLOCK_SYMBOLS = ['♠', '♥', '♣', '●', '▼', '■', '▲']
WALL_SYMBOL = 'X'
EMPTY_SYMBOL = '□'
CISCREENDW = 1

class CTetris(Tetris):
    @classmethod
    def init(cls, setOfBlockArrays):
        super().init(setOfBlockArrays)  
        cls.iScreenDw = 1              

    def __init__(self, cy, cx):
        self._iScreenDy = cy
        self._iScreenDx = cx
        self.iScreen = Matrix(Tetris.createArrayScreen(cy, cx, CISCREENDW)) 
        self.oScreen = Matrix(self.iScreen)
        self.top = 0
        self.left = 1 + cx // 2 - 2
        self.idxBlockType = 0
        self.idxBlockDegree = 0
        self.currBlk = None
        self.state = TetrisState.Running
        self.operation_table = dict()
        self.block_history = []

    def printScreen(self):
        temp = Matrix(self.oScreen)
        arr = temp.get_array()
        if self.currBlk is not None:
            blk_arr = self.currBlk.get_array()
            for y in range(self.currBlk.get_dy()):
                for x in range(self.currBlk.get_dx()):
                    ay = self.top + y
                    ax = self.left + x
                    if (0 <= ay < temp.get_dy()) and (0 <= ax < temp.get_dx()):
                        # 이 칸이 블록이면 타입번호(0~6)로 덮어
                        if blk_arr[y][x]:
                            arr[ay][ax] = self.idxBlockType + 10  # 임시로 10~16번 값으로 표기

        # 실제 출력

        for y in range(temp.get_dy()):
            for x in range(temp.get_dx()):
                v = arr[y][x]
                if v == 0:
                    print(EMPTY_SYMBOL, end='')
                elif v == 1: # 벽/바닥
                    print(WALL_SYMBOL, end='')
                elif v >= 10: # 현재 떨어지는 블록
                    print(BLOCK_SYMBOLS[v - 10], end='')
                elif 2 <= v <= 8: # 고정된 블록
                    print(BLOCK_SYMBOLS[v-2], end='')
                else:
                    print('?', end='') # 예외 상황
            print()
        print()

    # 블록 고정시 타입정보 저장
    def fixBlock(self):
        for y in range(self.currBlk.get_dy()):
            for x in range(self.currBlk.get_dx()):
                iy = self.top + y
                ix = self.left + x
                if self.currBlk.get_array()[y][x]:
                    if self.iScreen.get_array()[iy][ix] == 0:
                        self.iScreen.get_array()[iy][ix] = self.idxBlockType + 2
        self.oScreen = Matrix(self.iScreen)
    
    def anyConflict(self, top, left, currBlk):
        # 바운더리 체크
        if top < 0 or left < 0 or \
        (top + currBlk.get_dy()) > self.iScreen.get_dy() or \
        (left + currBlk.get_dx()) > self.iScreen.get_dx():
            return True
        # currBlk에서 1인 부분만 검사
        iScreenArr = self.iScreen.get_array()
        blkArr = currBlk.get_array()
        for y in range(currBlk.get_dy()):
            for x in range(currBlk.get_dx()):
                if blkArr[y][x]:
                    iy = top + y
                    ix = left + x
                    # 게임판에서 벽/바닥/고정 블록이 있는지 검사
                    if iScreenArr[iy][ix] > 0:
                        return True
        return False


if __name__ == "__main__":
    setOfBlockArrays = [
        # I
        [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
        # J
        [[1,0,0],[1,1,1],[0,0,0]],
        # L
        [[0,0,1],[1,1,1],[0,0,0]],
        # O
        [[1,1],[1,1]],
        # S
        [[0,1,1],[1,1,0],[0,0,0]],
        # T
        [[0,1,0],[1,1,1],[0,0,0]],
        # Z
        [[1,1,0],[0,1,1],[0,0,0]],
    ]
    CTetris.init(setOfBlockArrays)
    board = CTetris(15, 10)
    
    myOnLeft = MyOnLeft()
    myOnRight = MyOnRight()
    myOnDown = MyOnDown()
    myOnUp = MyOnUp()
    myOnDrop = MyOnDrop()
    myOnCw = MyOnCw()
    myOnCcw = MyOnCcw()
    myOnNewBlock = MyOnNewBlock()
    myOnFinished = MyOnFinished()

    board.setOperation('a', TetrisState.Running, myOnLeft, TetrisState.Running, myOnRight, TetrisState.Running)
    board.setOperation('d', TetrisState.Running, myOnRight, TetrisState.Running, myOnLeft, TetrisState.Running)
    board.setOperation('s', TetrisState.Running, myOnDown, TetrisState.Running, myOnUp, TetrisState.NewBlock)
    board.setOperation('w', TetrisState.Running, myOnCw, TetrisState.Running, myOnCcw, TetrisState.Running)
    board.setOperation(' ', TetrisState.Running, myOnDrop, TetrisState.Running, myOnUp, TetrisState.NewBlock)
    for n in '0123456':
        board.setOperation(n, TetrisState.NewBlock, myOnNewBlock, TetrisState.Running, myOnFinished, TetrisState.Finished)

    # 게임 실행 흐름 tetris_plugin 코드와 동일
    import random
    randomgen = random.Random()
    board.state = TetrisState.NewBlock
    key = str(randomgen.randint(0, 6))
    board.accept(key)
    board.printScreen()

    while True:
        key = input("Enter a key from [ q (quit), a (left), d (right), s (down), w (rotate), ' ' (drop) ] : ")
        if key == 'q':
            print("Program terminated!")
            break
        state = board.accept(key)
        if state == TetrisState.NewBlock:
            key = str(randomgen.randint(0, 6))
            state = board.accept(key)
        board.printScreen()
        if state == TetrisState.Finished:
            print("Game Over!")
            break
