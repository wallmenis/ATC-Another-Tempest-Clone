import pygame
from sys import exit
import xml.etree.ElementTree as ET
import re
import numpy as np

# Default parameters
global resolution, dpi
dpi = 96
resolution = (800, 600)


def importPolygonFromSvg(svgfile):
    levelTree = ET.parse(svgfile)
    levelRoot = levelTree.getroot()
    print()
    path = "./g/path"
    path = re.sub("/", "/{http://www.w3.org/2000/svg}", path)
    levelGeom = levelRoot.find(path).attrib["d"]
    # levelGeom.pop(len(levelGeom) - 1)
    levelGeom = re.sub("[zlLZ]", "", levelGeom)
    levelGeom = " ".join(levelGeom.split())
    print(levelGeom)
    levelGeom = levelGeom.split(" ")
    symbol = levelGeom.pop(0)
    print(levelGeom)
    tmpLevelGeom = []
    for i in levelGeom:
        tmpLevelGeom.append([float(i.split(",")[0]), float(i.split(",")[1])])
    levelGeom = milimetersToPixels(np.array(tmpLevelGeom.copy()))
    if symbol == "m":
        levelGeom = np.cumsum(levelGeom, axis=0)
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

    def __str__(self):
        iscyc = ""
        tmpcyc = self.cycle
        if self.cycle > 0:
            iscyc = "not "
        else:
            tmpcyc = tmpcyc * (-1)
        return f"Player in position {self.position} in level with {tmpcyc} positions that is {iscyc}cyclical. Points making the shape: {self.pointList}"


class Level:
    def __init__(self, lvlnum, enLst, svgfile):
        self.levelNumber = lvlnum
        self.enemyList = enLst
        self.polygonPoints = importPolygonFromSvg(svgfile)
        self.cyclical = self.importCyclicalFromSvg(svgfile)
        self.positions = self.getPositionsFromPolygon(self.polygonPoints)
        self.positionAngles = self.getPosAnglesFromPolygon(self.polygonPoints)

    def getPolygonPoints(self):
        return self.polygonPoints

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
        # print(self.positions[positionInLevel])
        # print(pointArray)
        objectCenter = np.sum(pArray, axis=0)/pArray.shape[0]
        pointArray = np.matmul(
            [np.cos(self.positionAngles[positionInLevel]), -np.sin(self.positionAngles[positionInLevel]),]

            )
        endPosition = []
        for i in pointArray:
            # print(i)
            endPosition.append(np.array(i) + self.positions[positionInLevel] - objectCenter)
        endPosition = np.array(endPosition)
        return endPosition

    def getPosAnglesFromPolygon(self, polygonPoints):
        angles = []
        print("test")
        for i in range(len(polygonPoints) - 1):
            tmpangle = polygonPoints[i] - polygonPoints[i+1]
            if tmpangle[1] == 0:
                tmpangle = 0
            elif tmpangle[0] == 0:
                tmpangle = np.pi/2.0
            else:
                tmpangle = tmpangle[1]/tmpangle[0]
            angles.append(tmpangle)
        if self.cyclical is True:
            print("is cyclical")
            tmpangle = polygonPoints[0] - polygonPoints[len(polygonPoints) - 1]
            if tmpangle[1] == 0:
                tmpangle = 0
            elif tmpangle[0] == 0:
                tmpangle = np.pi/2.0
            else:
                tmpangle = tmpangle[1]/tmpangle[0]
            angles.append(tmpangle)
        return angles

    def __str__(self):
        iscyc = ""
        if not self.cyclical:
            iscyc = "not "
        return f"Level with number {self.levelNumber} and {self.positions} positions that is {iscyc}cyclical. Points making the shape: {self.polygonPoints}, Enemy list: {self.enemyList}"


def scaleAgainstCenter(scale, polygonPoints, center):
    objectCenter = np.sum(polygonPoints, axis = 0)/polygonPoints.shape[0]
    # print(f"center:  {objectCenter}")
    scaled = (polygonPoints - objectCenter)*scale + objectCenter
    scaled += center
    return scaled


def milimetersToPixels(pointArray):
    return pointArray*dpi*0.03937008


def drawLinesForLevel(polygonPoints, scaledPolygonPoints, screen, color, width):
    for i in range(polygonPoints.shape[0]):
        pygame.draw.line(screen, color, polygonPoints[i], scaledPolygonPoints[i], width)


def DrawGame(player, level, screen):
    # pygame.draw.polygon(screen, ())
    scaled = scaleAgainstCenter(0.1, level.polygonPoints, np.array([0, 0]))
    pygame.draw.polygon(screen, (255, 255, 255), level.getPolygonPoints(), 1)
    pygame.draw.polygon(screen, (255, 255, 255), scaled, 1)
    # print(level.localToLevelSpace(player.position, player.pointList))
    pygame.draw.polygon(screen, (0, 255, 0), level.localToLevelSpace(player.position, player.pointList), 1)
    drawLinesForLevel(level.getPolygonPoints(), scaled, screen, (255, 255, 255), 1)


def DrawMainMenu():
    option = False
    return option


def DrawPauseMenu():
    option = False
    return option


LevelList = []
LevelList.append(Level(1, [], "testsvg.svg"))

BaseLevel = LevelList[0]
BasePlayer = Player(BaseLevel.getCyclicalForPlayer(), "Player.svg")

print(BaseLevel)
print(BasePlayer)

pygame.init()
screen = pygame.display.set_mode(resolution)  # Set Resolution    h,w
pygame.display.set_caption("Another Tempest Clone")  # Sets Name For The Game
clock = pygame.time.Clock()  # Object To Control The Framerate

BaseSurface = pygame.Surface(resolution)
screen.fill("black")

while True:
    for event in pygame.event.get():  # Checks for Events From Keyboard Or Mouse
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_LEFT:
                    BasePlayer.moveLeft()
                case pygame.K_RIGHT:
                    BasePlayer.moveRight()
            print(BasePlayer)
    screen.fill("black")
    DrawGame(BasePlayer, BaseLevel, screen)
    DrawPauseMenu()
    DrawMainMenu()
    # print("screen")
    # pygame.display.update()
    pygame.display.flip()
    clock.tick(60)  # 60 Frames/Second
