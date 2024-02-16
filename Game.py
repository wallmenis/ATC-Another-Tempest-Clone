import pygame
from sys import exit
import xml.etree.ElementTree as ET
import re
import numpy as np

# Default parameters
global resolution, dpi
dpi = 96
resolution = (800, 600)


class Player:
    def __init__(self, c):
        self.position = 0  # The game is effectively cyclical 2D as far as the position.
        self.cycle = c  # It is cyclical but some levels arent so we will set negative values for noncyclical levels
        self.pointList = np.array([[2, 0, 1], [2, 0, 0], [-2, 0, -1]])
        self.movablePoint = 0

    def moveLeft(self):
        nocyc = 0
        cycle = self.cycle
        if self.cycle < 0:
            nocyc = 1
            cycle = cycle * (-1)
        position = self.position + 1
        if position > cycle:
            position = position - 1
            if nocyc == 0:
                position = 0
        self.position = position

    def moveRight(self):
        nocyc = 0
        cycle = self.cycle
        if self.cycle < 0:
            nocyc = 1
            cycle = cycle * (-1)
        position = self.position - 1
        if position < 0:
            position = position + 1
            if nocyc == 0:
                position = cycle
        self.position = position

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
        self.polygonPoints = self.importPolygonFromSvg(svgfile)
        self.cyclical = self.importCyclicalFromSvg(svgfile)
        self.positions = self.getPositionsFromPolygon(self.polygonPoints)

    def getPolygonPoints(self):
        return self.polygonPoints

    def importPolygonFromSvg(self, svgfile):
        levelTree = ET.parse(svgfile)
        levelRoot = levelTree.getroot()
        print()
        path = "./g/path"
        path = re.sub("/", "/{http://www.w3.org/2000/svg}", path)
        levelGeom = levelRoot.find(path).attrib["d"].split(" ")
        levelGeom.pop(0)
        levelGeom.pop(len(levelGeom) - 1)
        tmpLevelGeom = []
        for i in levelGeom:
            tmpLevelGeom.append([float(i.split(",")[0]), float(i.split(",")[1])])
        levelGeom = milimetersToPixels(np.array(tmpLevelGeom.copy()))
        return levelGeom

    def importCyclicalFromSvg(self, svgfile):
        levelTree = ET.parse(svgfile)
        levelRoot = levelTree.getroot()
        path = "./g/text"
        path = re.sub("/", "/{http://www.w3.org/2000/svg}", path)
        levelCyc = levelRoot.find(path)
        if levelCyc == "None":
            return True
        return False

    def generateScaledPolygonVerts(self, scale):
        tmpScaled = []
        for i in self.polygonPoints:
            tmpScaled.append(np.array(i) - np.array(resolution)/2)

        scaled = self.polygonPoints*scale
        return scaled

    def getPositionsFromPolygon(self, polygonPoints):
        positions = []
        for i in range(len(polygonPoints) - 1):
            positions.append((polygonPoints[i] + polygonPoints[i + 1]) / 2.0)
        if bool(self.cyclical):
            positions.append(
                (polygonPoints[0] + polygonPoints[len(polygonPoints) - 1]) / 2.0
            )
        return positions

    def getCyclicalForPlayer(self):
        if not self.cyclical:
            return (-1) * len(self.getPolygonPoints())
        return len(self.getPolygonPoints())

    def localToLevelSpace(self, positionInLevel, pointArray):
        print(self.positions[positionInLevel])
        print(pointArray)
        endPosition = []
        for i in pointArray:
            print(i)
            endPosition.append(np.array(i) + self.positions[positionInLevel])
        endPosition = np.array(endPosition)
        return endPosition

    def __str__(self):
        iscyc = ""
        if not self.cyclical:
            iscyc = "not "
        return f"Level with number {self.levelNumber} and {self.positions} positions that is {iscyc}cyclical. Points making the shape: {self.polygonPoints}, Enemy list: {self.enemyList}"


def milimetersToPixels(pointArray):
    return pointArray*dpi*0.03937008


def DrawGame(player, level, screen):
    # pygame.draw.polygon(screen, ())
    pygame.draw.polygon(screen, (255, 255, 255), level.getPolygonPoints(), 1)
    pygame.draw.polygon(screen, (0, 255, 0), level.localToLevelSpace(player.position, player.pointList))


def DrawMainMenu():
    option = False
    return option


def DrawPauseMenu():
    option = False
    return option


LevelList = []
LevelList.append(Level(1, [], "testsvg.svg"))

BaseLevel = LevelList[0]
BasePlayer = Player(BaseLevel.getCyclicalForPlayer())

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
    DrawGame(BasePlayer, BaseLevel, screen)
    DrawPauseMenu()
    DrawMainMenu()
    # print("screen")
    pygame.display.update()
    # pygame.display.flip()
    clock.tick(60)  # 60 Frames/Second
