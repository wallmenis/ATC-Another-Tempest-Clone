from sys import exit
import xml.etree.ElementTree as ET
import os
from sys import platform
import re
import shutil
try:
    import pygame
    import svg.path
    import numpy as np
except:
    if not os.path.isdir("gameEnv"):
        os.system("python3 -m venv gameEnv")
        if platform == "win32":
            os.system("gameEnv\\bin\\python -m pip install pygame svg.path numpy") # reminder to use os.path next time
            os.system("gameEnv\\bin\\python Game.py")
        else:
            os.system("gameEnv/bin/python -m pip install pygame svg.path numpy")
            os.system("gameEnv/bin/python Game.py")
        exit()
    try:
        import pygame
        import svg.path
        import numpy as np
    except:
        shutil.rmtree("gameEnv")
        os.system("python3 -m venv gameEnv")
        if sys.platform == "win32":
            os.system("gameEnv\\bin\\python -m pip install pygame svg.path numpy")
            os.system("gameEnv\\bin\\python Game.py")
        else:
            os.system("gameEnv/bin/python -m pip install pygame svg.path numpy")
            os.system("gameEnv/bin/python Game.py")
        exit()

# Default parameters
global resolution, dpi, play_mode, sensitivity
dpi = 96
resolution = np.array((1280, 720))
play_mode = "Demo"
sensitivity = 0.2

# def importPolygonFromSvg(svgfile):
#     levelTree = ET.parse(svgfile)
#     levelRoot = levelTree.getroot()
#     print()
#     path = "./g/path"
#     path = re.sub("/", "/{http://www.w3.org/2000/svg}", path)
#     levelGeom = levelRoot.find(path).attrib["d"]
#     # levelGeom.pop(len(levelGeom) - 1)
#     levelGeom = re.sub("[zlLZ]", "", levelGeom)
#     levelGeom = " ".join(levelGeom.split())
#     print(levelGeom)
#     levelGeom = levelGeom.split(" ")
#     symbol = levelGeom.pop(0)
#     print(levelGeom)
#     tmpLevelGeom = []
#     for i in levelGeom:
#         tmpLevelGeom.append([float(i.split(",")[0]), float(i.split(",")[1])])
#     levelGeom = milimetersToPixels(np.array(tmpLevelGeom.copy()))
#     if symbol == "m":
#         levelGeom = np.cumsum(levelGeom, axis=0)
#     return levelGeom

def importPolygonFromSvg(svgfile):
    levelTree = ET.parse(svgfile)
    levelRoot = levelTree.getroot()
    print()
    path = "./g/path"
    path = re.sub("/", "/{http://www.w3.org/2000/svg}", path)
    levelPath = levelRoot.find(path).attrib["d"]
    pp = svg.path.parse_path(levelPath)
    points = []
    pp.pop(0)
    # topLeft = [pp[0].point(0).real, pp[0].point(0).imag]
    # for i in pp:
    #     if i.point(0).real + i.point(0).imag < topLeft[0] + topLeft[1]:
    #         topLeft = [i.point(0).real, i.point(0).imag]
    # print(f"topLeft{topLeft}")
    counter = 0
    s = [0, 0]
    for i in pp:
        s = [s[0] + i.point(0).real, s[1] + i.point(0).imag]
        counter += 1
    s = [s[0]/counter, s[1]/counter]
    for i in pp:
        points.append([i.point(0).real - s[0], i.point(0).imag - s[1]])
    points = np.array(points)
    points = milimetersToPixels(points)
    levelGeom = []
    for i in points:
        levelGeom.append(i + resolution/2.0)
    levelGeom = np.array(levelGeom)
    return levelGeom


class Player:
    def __init__(self, c, svgfile):
        self.position = 0  # The game is effectively cyclical 2D as far as the position.
        self.cycle = c  # It is cyclical but some levels arent so we will set negative values for noncyclical levels
        self.pointList = importPolygonFromSvg(svgfile)
        self.depth = 0

    def moveLeft(self):
        nocyc = 0
        tmpcycle = self.cycle
        if self.cycle < 0:
            nocyc = 1
            tmpcycle = tmpcycle * (-1)
        tmpposition = self.position + 1
        if tmpposition > tmpcycle - 1:
            tmpposition = tmpposition - 1
            if nocyc == 1:
                tmpposition = 0
        self.position = tmpposition

    def moveRight(self):
        nocyc = 0
        tmpcycle = self.cycle
        if self.cycle < 0:
            nocyc = 1
            tmpcycle = tmpcycle * (-1)
        tmpposition = self.position - 1
        if tmpposition < 0:
            tmpposition = tmpposition + 1
            if nocyc == 1:
                tmpposition = tmpcycle - 1
        self.position = tmpposition

    def refreshForResolution(self):
        points = []
        center = np.sum(self.pointList, axis=0)/pointList.shape[0]
        for i in self.pointList:
            points.append(i - center + resolution/2.0)
        self.pointList = np.array(points)

    def __str__(self):
        iscyc = ""
        tmpcyc = self.cycle
        if self.cycle > 0:
            iscyc = "not "
        else:
            tmpcyc = tmpcyc * (-1)
        return f"Player in position {self.position} in level with {tmpcyc} positions that is {iscyc}cyclical. Points making the shape: {self.pointList}"


class Level:
    def __init__(self, lvlnum, enLst, svgfile, color):
        self.levelNumber = lvlnum
        self.enemyList = enLst
        self.polygonPoints = importPolygonFromSvg(svgfile)
        self.cyclical = self.importCyclicalFromSvg(svgfile)
        self.positions = self.getPositionsFromPolygon(self.polygonPoints)
        self.positionAngles = self.getPosAnglesFromPolygon(self.polygonPoints)
        self.color = color

    def importCyclicalFromSvg(self, svgfile):
        levelTree = ET.parse(svgfile)
        levelRoot = levelTree.getroot()
        path = "./g/text"
        path = re.sub("/", "/{http://www.w3.org/2000/svg}", path)
        levelCyc = levelRoot.find(path)
        if levelCyc is None:
            return True
        return False

    def getPositionsFromPolygon(self, polygonPoints):
        positions = []
        print("test")
        for i in range(len(polygonPoints) - 1):
            positions.append((polygonPoints[i] + polygonPoints[i + 1]) / 2.0)
        if self.cyclical is True:
            print("is cyclical")
            positions.append(
                (polygonPoints[0] + polygonPoints[len(polygonPoints) - 1]) / 2.0
            )
        return positions

    def getCyclicalForPlayer(self):
        if not self.cyclical:
            return len(self.positions)
        return (-1) * len(self.positions)

    def localToLevelSpace(self, positionInLevel, pArray):
        print(self.positionAngles[positionInLevel])
        # print(pointArray)
        objectCenter = np.sum(pArray, axis=0)/pArray.shape[0]
        sines = np.sin(self.positionAngles[positionInLevel])
        cosines = np.cos(self.positionAngles[positionInLevel])
        pointArray = []
        for i in pArray:
            tmp = np.array(i) - objectCenter
            tmp = np.matmul([[cosines, -sines], [sines, cosines]], tmp)
            pointArray.append(tmp)
        endPosition = []
        for i in pointArray:
            # print(i)
            endPosition.append(np.array(i) + self.positions[positionInLevel])
        endPosition = np.array(endPosition)
        return endPosition

    def getPosAnglesFromPolygon(self, polygonPoints):
        angles = []
        # print("test")
        for i in range(len(polygonPoints) - 1):
            tmpangle = polygonPoints[i] - polygonPoints[i+1]
            slope = polygonPoints[i] - polygonPoints[i+1]
            # tmpangle = (-1)*tmpangle
            print(f"slope {tmpangle}")
            if tmpangle[1] == 0:
                tmpangle = 0
            elif tmpangle[0] == 0:
                tmpangle = np.pi/2.0
            else:
                tmpangle = np.arctan(tmpangle[1]/tmpangle[0])
            if slope[0] < 0:
                tmpangle += np.pi
            # tmpangle = rotateIfLookingAway(tmp, center, tmpangle)
            angles.append(tmpangle)
        if self.cyclical is True:
            tmpangle = polygonPoints[0] - polygonPoints[len(polygonPoints) - 1]
            slope = polygonPoints[0] - polygonPoints[len(polygonPoints) - 1]
            # tmpangle = (-1)*tmpangle
            print(f"slope {tmpangle}")
            if tmpangle[1] == 0:
                tmpangle = 0
            elif tmpangle[0] == 0:
                tmpangle = np.pi/2.0
            else:
                tmpangle = np.arctan(tmpangle[1]/tmpangle[0])
            if slope[0] < 0:
                tmpangle += np.pi
            # tmpangle = rotateIfLookingAway(tmp, center, tmpangle)
            angles.append(tmpangle)
        angles = np.array(angles)
        print(f"Angles {angles*360/np.pi}")
        return angles

    def refreshForResolution(self):
        points = []
        center = np.sum(self.polygonPoints, axis=0)/self.polygonPoints.shape[0]
        for i in self.pointList:
            points.append(i - center + resolution/2.0)
        self.polygonPoints = np.array(points)

    def __str__(self):
        iscyc = ""
        if not self.cyclical:
            iscyc = "not "
        return f"Level with number {self.levelNumber} and {self.positions} positions that is {iscyc}cyclical. Points making the shape: {self.polygonPoints}, Enemy list: {self.enemyList}"


class Enemy(Player):
    def __init__(self, c, svgfile, spawndepth, spawnpos):
        self.position = spawnpos  # The game is effectively cyclical 2D as far as the position.
        self.cycle = c  # It is cyclical but some levels arent so we will set negative values for noncyclical levels
        self.pointList = importPolygonFromSvg(svgfile)
        self.depth = spawndepth


def rotateIfLookingAway(point1, center, angle):
    newAngle = angle
    if point1[0] < center[0] and point1[1] < center[1]:
        if angle < 0 or angle > np.pi/4:
            newAngle += np.pi
    if point1[0] > center[0] and point1[1] < center[1]:
        if angle < 0 or angle < np.pi/4:
            newAngle += np.pi
    if point1[0] > center[0] and point1[1] > center[1]:
        if angle > 0 or angle < -np.pi/4:
            newAngle += np.pi
    if point1[0] < center[0] and point1[1] > center[1]:
        if angle > 0 or angle > -np.pi/4:
            newAngle += np.pi
    return newAngle


def scaleAgainstCenter(scale, polygonPoints, center):
    objectCenter = np.sum(polygonPoints, axis=0)/polygonPoints.shape[0]
    # print(f"center:  {objectCenter}")
    scaled = (polygonPoints - objectCenter)*scale + objectCenter
    scaled += center
    return scaled


def milimetersToPixels(pointArray):
    return pointArray*dpi*0.03937008


def drawLinesForLevel(polygonPoints, scaledPolygonPoints, screen, color, width):
    for i in range(polygonPoints.shape[0]):
        pygame.draw.line(screen, color, polygonPoints[i], scaledPolygonPoints[i], width)


def cameraPOVtransformation(cameraPos, polygonPoints, depth, d):
    newPoints = []
    output = []
    center = np.sum(polygonPoints, axis=0)/polygonPoints.shape[0]
    for i in polygonPoints:
        newPoints.append(i - center + cameraPos)
    newPoints = np.array(newPoints)
    transformationMatrix = [
        [d, 0, 0, 0],
        [0, d, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 1, d]
        ]
    transformationMatrix = np.array(transformationMatrix)
    newPoints3D = []
    for i in newPoints:
        # print(f"i={i}")
        newPoints3D.append([i[0], i[1], depth, 1])
    # print(f"newPoints3D{newPoints3D}")
    newPoints3D = np.array(newPoints3D)
    newPoints = np.matmul(newPoints3D, transformationMatrix)
    # print(f"newPoints{newPoints}")
    for i in newPoints:
        # print(f"i3={i[3]}")
        output.append(np.array([i[0]/(d+depth), i[1]/(d+depth)]) + center)
    output = np.array(output)
    return output


def accelerateCam(player, level, cameraPos, velocity):
    cameraP = cameraPos
    ppos = level.positions[player.position]
    center = np.sum(level.polygonPoints, axis=0)/level.polygonPoints.shape[0]
    cameraWish = (center-ppos)/(2) - cameraP
    # print(ppos)
    # print(cameraWish)
    if 0 != cameraWish[0] or 0 != cameraWish[1]:
        cameraP = cameraP + (cameraWish)*velocity
    return cameraP


def DrawGame(player, level, screen, cameraP):
    # pygame.draw.polygon(screen, ())
    ppos = level.localToLevelSpace(player.position, player.pointList)

    # scaled = scaleAgainstCenter(0.1, level.polygonPoints, np.array([cameraPos[0], cameraPos[1]]))
    scaled = cameraPOVtransformation(cameraPos, level.polygonPoints, 10, 1)
    front = cameraPOVtransformation(cameraPos, level.polygonPoints, 0, 1)

    ppos = cameraPOVtransformation(cameraPos, ppos, 0, 1)
    pygame.draw.polygon(screen, level.color, front, 1)
    pygame.draw.polygon(screen, level.color, scaled, 1)
    pygame.draw.polygon(screen, (0, 255, 0), ppos, 1)
    drawLinesForLevel(front, scaled, screen, level.color, 1)


def DrawMainMenu():
    option = False
    return option


def DrawPauseMenu():
    option = False
    return option


LevelList = []
LevelList.append(Level(1, [], "Level1.svg", (0, 0, 255)))

BaseLevel = LevelList[0]
BasePlayer = Player(BaseLevel.getCyclicalForPlayer(), "Player.svg")
# PletList

print(BaseLevel)
print(BasePlayer)

pygame.init()
screen = pygame.display.set_mode(resolution)  # Set Resolution    h,w
pygame.display.set_caption("Another Tempest Clone")  # Sets Name For The Game
clock = pygame.time.Clock()  # Object To Control The Framerate

BaseSurface = pygame.Surface(resolution)
screen.fill("black")
cameraPos = np.array([0, 0])
wishVector = 0
while True:
    for event in pygame.event.get():  # Checks for Events From Keyboard Or Mouse
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        # if event.type == pygame.KEYDOWN:
        #     match event.key:
        #         case pygame.K_LEFT:
        #             BasePlayer.moveLeft()
        #         case pygame.K_RIGHT:
        #             BasePlayer.moveRight()
        #     print(BasePlayer)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        wishVector -= sensitivity
    if keys[pygame.K_RIGHT]:
        wishVector += sensitivity
    if wishVector < -1:
        BasePlayer.moveLeft()
        wishVector = 0
    if wishVector > 1:
        BasePlayer.moveRight()
        wishVector = 0
    screen.fill("black")
    cameraPos = accelerateCam(BasePlayer, BaseLevel, cameraPos, 0.4)
    DrawGame(BasePlayer, BaseLevel, screen, cameraPos)
    DrawPauseMenu()
    DrawMainMenu()
    # print("screen")
    # pygame.display.update()
    # cameraP[0] += 1
    # cameraP[1] += 1
    pygame.display.flip()
    clock.tick(60)  # 60 Frames/Second
