#tetris_plugin.py

from enum import Enum
from abc import ABC, abstractmethod
import random
from matrix import Matrix

# 변경된 회전 알고리즘
def rotate_cw(arr):
    n = len(arr) # 행의 개수 
    m = len(arr[0]) # 열의 개수
    # m x n 배열로 새로 만듦 (원본이 n x m이면)
    new_arr = [[0] * n for _ in range(m)]
    for i in range(n):       
        for j in range(m):  
            new_arr[j][n - 1 - i] = arr[i][j]
    return new_arr


def rotate_ccw(arr):
    n = len(arr) # 행의 개수 
    m = len(arr[0]) # 열의 개수
    new_arr = [[0] * n for _ in range(m)]
    for i in range(n):      
        for j in range(m):   
            new_arr[m - 1 - j][i] = arr[i][j]
    return new_arr

class TetrisState(Enum):
    Running = 0
    NewBlock = 1
    Finished = 2

# 핸들러 추상 클래스
class OnLeft(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

class OnRight(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

class OnDown(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

class OnUp(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

class OnDrop(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

class OnCw(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

class OnCcw(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

class OnNewBlock(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

class OnFinished(ABC):
    @abstractmethod
    def run(self, t, key):
        pass

# 핸들러 구현
class MyOnLeft(OnLeft):
    def run(self, t, key):
        t.left -= 1
        return t.anyConflict(t.top, t.left, t.currBlk)

class MyOnRight(OnRight):
    def run(self, t, key):
        t.left += 1
        return t.anyConflict(t.top, t.left, t.currBlk)

class MyOnDown(OnDown):
    def run(self, t, key):
        t.top += 1
        # 충돌은 accept에서 처리
        return t.anyConflict(t.top, t.left, t.currBlk)

class MyOnDrop(OnDrop):
    def run(self, t, key):
        while True:
            t.top += 1
            if t.anyConflict(t.top, t.left, t.currBlk):
                # top -= 1  # undo 하지 않음!
                return True

class MyOnUp(OnUp):
    def run(self, t, key):
        t.top -= 1
        return False

class MyOnCw(OnCw):
    def run(self, t, key):
        prevDegree = t.idxBlockDegree
        t.idxBlockDegree = (t.idxBlockDegree + 1) % t.nBlockDegrees
        arr = t.setOfBlockObjects[t.idxBlockType]
        rotated_arr = t.get_rotated_block(t.idxBlockType, arr, t.idxBlockDegree, clockwise=True)
        t.currBlk = Matrix(rotated_arr)
        conflict = t.anyConflict(t.top, t.left, t.currBlk)
        # 충돌 발생시 degree/blk는 변경된 상태로 놔둔다
        return conflict

class MyOnCcw(OnCcw):
    def run(self, t, key):
        t.idxBlockDegree = (t.idxBlockDegree - 1) % t.nBlockDegrees
        arr = t.setOfBlockObjects[t.idxBlockType]
        rotated_arr = t.get_rotated_block(t.idxBlockType, arr, t.idxBlockDegree, clockwise=True)
        t.currBlk = Matrix(rotated_arr)
        return False  # 복구만

class MyOnNewBlock(OnNewBlock):
    def run(self, t, key):
        t.deleteFullLines()
        t.iScreen = Matrix(t.oScreen)
        t.idxBlockType = int(key)
        t.idxBlockDegree = 0
        arr = t.setOfBlockObjects[t.idxBlockType]
        rotated_arr = t.get_rotated_block(t.idxBlockType, arr, t.idxBlockDegree, clockwise=True)
        t.currBlk = Matrix(rotated_arr)
        t.top = 0
        t.left = t.iScreenDw + t._iScreenDx // 2 - (t.currBlk.get_dx() + 1) // 2
        return t.anyConflict(t.top, t.left, t.currBlk)

class MyOnFinished(OnFinished):
    def run(self, t, key):
        return False


class Tetris:
    nBlockTypes = 0
    nBlockDegrees = 0
    setOfBlockObjects = None
    iScreenDw = 0 # 클래스 변수에 추가함

    @classmethod
    def init(cls, setOfBlockArrays):
        cls.nBlockTypes = len(setOfBlockArrays)
        cls.nBlockDegrees = 4
        cls.setOfBlockObjects = setOfBlockArrays
        cls.iScreenDw = 4

    def __init__(self, cy, cx):
        self._iScreenDy = cy
        self._iScreenDx = cx
        self.iScreen = Matrix(Tetris.createArrayScreen(cy, cx, Tetris.iScreenDw))
        self.oScreen = Matrix(self.iScreen)
        self.top = 0
        self.left = Tetris.iScreenDw + cx // 2 - 2
        self.idxBlockType = 0
        self.idxBlockDegree = 0
        self.currBlk = None
        self.state = TetrisState.Running
        self.operation_table = dict()  

    @staticmethod
    def createArrayScreen(dy, dx, dw):
        array = []
        for y in range(dy):
            array.append([1]*dw + [0]*dx + [1]*dw)
        for _ in range(dw):
            array.append([1]*(dx + 2*dw))
        return array

    def setOperation(self, key, cur_state, do_handler, next_state, undo_handler, next_state_undo):
        if key not in self.operation_table:
            self.operation_table[key] = {}
        self.operation_table[key][cur_state] = (do_handler, next_state, undo_handler, next_state_undo)

    def accept(self, key, undo=False):
        op = self.operation_table.get(key, {}).get(self.state)
        if not op:
            print("Invalid key/state: ", key, self.state)
            return self.state
        do_handler, next_state, undo_handler, next_state_undo = op
        if not undo:
            is_conflict = do_handler.run(self, key)
            if is_conflict:
                if undo_handler:
                    undo_handler.run(self, key)  
            # 여기서 key별로 분기
            if key in [' ', 's']:
                if is_conflict:
                    self.fixBlock()   
                    self.state = TetrisState.NewBlock
                else:
                    self.state = TetrisState.Running
            else:
                self.state = TetrisState.Running
        else:
            if undo_handler: undo_handler.run(self, key)
            self.state = next_state_undo
        return self.state



    def printScreen(self):
        temp = Matrix(self.oScreen)
        if self.currBlk is not None:
            arr = temp.get_array()
            blk_arr = self.currBlk.get_array()
            for y in range(self.currBlk.get_dy()):
                for x in range(self.currBlk.get_dx()):
                    ay = self.top + y
                    ax = self.left + x
                    if (0 <= ay < temp.get_dy()) and (0 <= ax < temp.get_dx()):
                        arr[ay][ax] += blk_arr[y][x]
        Tetris.printMatrixScreen(temp)

    @staticmethod
    def printMatrixScreen(screen):
        array = screen.get_array()
        for y in range(screen.get_dy()):
            for x in range(screen.get_dx()):
                print('□' if array[y][x] == 0 else '■', end='')
            print()
        print()
    
    # 충돌 검사 함수
    # def anyConflict(self, top, left, currBlk):
    #     # 바운더리 체크(게임판 범위 벗어나면 무조건 충돌)
    #     if top < 0 or left < 0 or \
    #         (top + currBlk.get_dy()) > self.iScreen.get_dy() or \
    #         (left + currBlk.get_dx()) > self.iScreen.get_dx():
    #             return True
    #     temp = self.iScreen.clip(top, left, top + currBlk.get_dy(), left + currBlk.get_dx())
    #     temp = temp + currBlk
    #     arr = temp.get_array()
    #     for y in range(temp.get_dy()):
    #         for x in range(temp.get_dx()):
    #             if arr[y][x] > 1:
    #                 return True
    #     return False

    def anyConflict(self, top, left, currBlk):
        temp = self.iScreen.clip(top, left, top + currBlk.get_dy(), left + currBlk.get_dx())
        temp = temp + currBlk
        arr = temp.get_array()
        for y in range(temp.get_dy()):
            for x in range(temp.get_dx()):
                if arr[y][x] > 1:
                    # 바닥/벽/블록 구분 없이 무조건 1(True) 반환
                    return True
        return False


    # def deleteFullLines(self):
    #     array = self.iScreen.get_array()
    #     dy, dx, dw = self._iScreenDy, self._iScreenDx, self.iScreenDw
    #     full_lines = []
    #     for y in range(dy):
    #         if all(array[y][dw:dw+dx]):
    #             full_lines.append(y)
    #     for y in reversed(full_lines):
    #         del array[y]
    #         array.insert(0, [1]*dw + [0]*dx + [1]*dw)
    #     self.iScreen = Matrix(array)
    #     self.oScreen = Matrix(array)

    def deleteFullLines(self):
        array = self.iScreen.get_array()
        dy, dx, dw = self._iScreenDy, self._iScreenDx, self.iScreenDw

        currBlk = self.currBlk
        top = self.top
        if currBlk is None:
            return
        
        result = []
        n_total = dy + dw
        affected_rows = set(range(top, top + currBlk.get_dy()))

        for y in range(dy):
            if y in affected_rows:
                if all(array[y][dw:dw+dx]):
                    continue
            result.append([1]*dw + array[y][dw:dw+dx] + [1]*dw)

        n_deleted = dy - len(result)
        empty_line = [1]*dw + [0]*dx + [1]*dw
        for _ in range(n_deleted):
            result.insert(0, empty_line[:])  

        for y in range(dy, n_total):
            result.append([1]*(dx+2*dw))

        self.iScreen = Matrix(result)
        self.oScreen = Matrix(result)



    def fixBlock(self):
        for y in range(self.currBlk.get_dy()):
            for x in range(self.currBlk.get_dx()):
                if self.currBlk.get_array()[y][x]:
                    self.iScreen.get_array()[self.top + y][self.left + x] = 1
            self.oScreen = Matrix(self.iScreen)
            self.deleteFullLines()  # 블록 고정 후 곧장 줄 삭제되도록

    def get_rotated_block(self, idxBlockType, arr, degree, clockwise=True):
        if idxBlockType == 3:  # O블록 예외
            return arr
        rotated = arr
        degree = degree % self.nBlockDegrees
        if clockwise:
            for _ in range(degree):
                rotated = rotate_cw(rotated)
        else:
            for _ in range(degree):
                rotated = rotate_ccw(rotated)
        return rotated

def getKey():
    key = input("Enter a key from [ q (quit), a (left), d (right), s (down), w (rotate), ' ' (drop) ] : ")

    if key == '':
        return ' '
    return key[0]

if __name__ == "__main__":
    setOfBlockArrays = [
    # I
    [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
    # J
    [[1,0,0],[1,1,1],[0,0,0]],
    # L
    [[0,0,1],[1,1,1],[0,0,0]],
    # O
    [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
    # S
    [[0,1,1],[1,1,0],[0,0,0]],
    # T
    [[0,1,0],[1,1,1],[0,0,0]],
    # Z
    [[1,1,0],[0,1,1],[0,0,0]],
]
    Tetris.init(setOfBlockArrays)
    board = Tetris(15, 10)
    randomgen = random.Random()

    # 핸들러 인스턴스 생성
    myOnLeft = MyOnLeft()
    myOnRight = MyOnRight()
    myOnDown = MyOnDown()
    myOnUp = MyOnUp()
    myOnDrop = MyOnDrop()
    myOnCw = MyOnCw()
    myOnCcw = MyOnCcw()
    myOnNewBlock = MyOnNewBlock()
    myOnFinished = MyOnFinished()

    # setOperation 설정
    board.setOperation('a', TetrisState.Running, myOnLeft, TetrisState.Running, myOnRight, TetrisState.Running)
    board.setOperation('d', TetrisState.Running, myOnRight, TetrisState.Running, myOnLeft, TetrisState.Running)
    board.setOperation('s', TetrisState.Running, myOnDown, TetrisState.Running, myOnUp, TetrisState.NewBlock)
    board.setOperation('w', TetrisState.Running, myOnCw, TetrisState.Running, myOnCcw, TetrisState.Running)
    board.setOperation(' ', TetrisState.Running, myOnDrop, TetrisState.Running, myOnUp, TetrisState.NewBlock)
    for n in "0123456":
        board.setOperation(n, TetrisState.NewBlock, myOnNewBlock, TetrisState.Running, myOnFinished, TetrisState.Finished)

    # 게임 실행
    board.state = TetrisState.NewBlock
    key = str(randomgen.randint(0, 6))
    board.accept(key)
    board.printScreen()

    while True:
        key = getKey()
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
