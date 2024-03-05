from sys import exit
import xml.etree.ElementTree as ET
import re
from enum import Enum
import random as rnd
import pygame
import svg.path
import numpy as np
import copy
import time
# from numba import jit


# @jit
def milimetersToPixels(pointArray):
    return pointArray * dpi * 0.03937008


def importPolygonFromSvg(svgfile):
    levelTree = ET.parse(svgfile)
    levelRoot = levelTree.getroot()
    path = "./g/path"
    path = re.sub("/", "/{http://www.w3.org/2000/svg}", path)
    levelPath = levelRoot.find(path).attrib["d"]
    pp = svg.path.parse_path(levelPath)
    points = []
    pp.pop(0)
    counter = 0
    s = [0, 0]
    for i in pp:
        s = [s[0] + i.point(0).real, s[1] + i.point(0).imag]
        counter += 1
    s = [s[0] / counter, s[1] / counter]
    for i in pp:
        points.append([i.point(0).real - s[0], i.point(0).imag - s[1]])
    points = np.array(points)
    points = milimetersToPixels(points)
    levelGeom = points
    return levelGeom


class PlayMode(Enum):
    PLAY = 0
    DEMO = 1
    CHANGELEVEL = 2
    PAUSE = 3


class EntityTag(Enum):
    PLAYER = 0
    ENEMY = 1


class Quadrant(Enum):
    FIRST = 0
    SECOND = 1
    THIRD = 2
    FOURTH = 3

# Default parameters
global resolution, dpi, playMode, sensitivity, shootCooldown, playDepth, deltaTime
dpi = 96
resolution = np.array((1280, 720))
playMode = PlayMode.DEMO
sensitivity = 0.2
shootCooldown = 0.2
playDepth = 10
cameraSpeed = 0.2
zoomSpeed = 0.1
endZoom = -20
startZoom = 5
invinsible = False

pygame.init()
#Sounds Initialization
shoot_effect = pygame.mixer.Sound("shoot_effect.mp3")
death_session = pygame.mixer.Sound("death_session.wav")
pause_session = pygame.mixer.Sound("pause_session.wav")
pew_session = pygame.mixer.Sound("pew_session.wav")

heart = importPolygonFromSvg("Heart.svg")
logo = importPolygonFromSvg("Logo.svg") # the logo wont work since the svg parser only reads the first path and not more


class Player:
    def __init__(self, c, svgfile, color, lives):
        self.position = 0  # The game is effectively cyclical 2D as far as the position.
        self.cycle = c  # It is cyclical but some levels arent so we will set negative values for noncyclical levels
        self.pointList = importPolygonFromSvg(svgfile)
        self.depth = 0
        self.color = color
        self.tag = EntityTag.PLAYER
        self.lives = lives

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

    def toCycle(self, inpPos):
        nocyc = 0
        tmpcycle = self.cycle
        if self.cycle < 0:
            nocyc = 1
            tmpcycle = tmpcycle * (-1)
        tmpposition = inpPos
        if nocyc == 1:
            if tmpposition < 0:
                tmpposition = tmpcycle - 1
            if tmpposition > tmpcycle - 1:
                tmpposition = 0
        else:
            if tmpposition < 0:
                tmpposition = 0
            if tmpposition > tmpcycle - 1:
                tmpposition = tmpcycle - 1
        return tmpposition

    def Shoot(self):
        return Projectile(
            self.position, self.depth - 1, 3, 1, (255, 255, 255), self.tag
        )

    def __str__(self):
        iscyc = ""
        tmpcyc = self.cycle
        if self.cycle > 0:
            iscyc = "not "
        else:
            tmpcyc = tmpcyc * (-1)
        return f"Player in position {self.position} in level with {tmpcyc} positions that is {iscyc}cyclical. Points making the shape: {self.pointList}"


class Level:
    def __init__(self, lvlnum, enLst, svgfile, color, concurrentEnemies):
        self.levelNumber = lvlnum
        self.enemyList = enLst
        self.polygonPoints = importPolygonFromSvg(svgfile)
        self.cyclical = self.importCyclicalFromSvg(svgfile)
        self.positions = self.getPositionsFromPolygon(self.polygonPoints)
        self.positionAngles = self.getPosAnglesFromPolygon(self.polygonPoints)
        self.color = color
        self.concurrentEnemies = concurrentEnemies
        self.makeOccupiedList()

    def getEmptyPosition(self):
        return self.occupiedList.tolist().index(0)

    def makeOccupiedList(self):
        ocList = np.zeros(len(self.positions), dtype = int)
        for i in range(min(len(self.enemyList), self.concurrentEnemies)):
            ocList[self.enemyList[i].position] += 1
            # print(self.enemyList[i].position)
        # print(f"ocList = {ocList}")
        self.occupiedList = ocList

    def checkIfOccupied(self, pos):
        return self.occupiedList[pos]

    def updateOccupiedList(self, prevpos, newpos):
        self.occupiedList[newpos] += 1
        # print(f"{self.occupiedList} {prevpos}")
        if self.occupiedList[prevpos] > 0:
            self.occupiedList[prevpos] -= 1

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
        # print("test")
        for i in range(len(polygonPoints) - 1):
            positions.append((polygonPoints[i] + polygonPoints[i + 1]) / 2.0)
        if self.cyclical is True:
            # print("is cyclical")
            positions.append(
                (polygonPoints[0] + polygonPoints[len(polygonPoints) - 1]) / 2.0
            )
        return positions

    def getCyclicalForPlayer(self):
        if not self.cyclical:
            return len(self.positions)
        return (-1) * len(self.positions)

    # @jit
    def localToLevelSpace(self, positionInLevel, pArray):
        objectCenter = np.sum(pArray, axis=0) / pArray.shape[0]
        sines = np.sin(self.positionAngles[positionInLevel])
        cosines = np.cos(self.positionAngles[positionInLevel])
        pointArray = []
        for i in pArray:
            tmp = np.array(i) - objectCenter
            tmp = np.matmul([[cosines, -sines], [sines, cosines]], tmp)
            pointArray.append(tmp)
        endPosition = []
        for i in pointArray:
            endPosition.append(np.array(i) + self.positions[positionInLevel])
        endPosition = np.array(endPosition)
        return endPosition

    def getPosAnglesFromPolygon(self, polygonPoints):
        angles = []
        for i in range(len(polygonPoints) - 1):
            tmpangle = polygonPoints[i] - polygonPoints[i + 1]
            slope = polygonPoints[i] - polygonPoints[i + 1]
            print(f"slope {tmpangle}")
            if tmpangle[1] == 0:
                tmpangle = 0
            elif tmpangle[0] == 0:
                tmpangle = np.pi / 2.0
            else:
                tmpangle = np.arctan(tmpangle[1] / tmpangle[0])
            # if slope[0] < 0:
            #     tmpangle += np.pi
            tmpangle = rotateIfLookingAway(slope, tmpangle)
            angles.append(tmpangle)
        if self.cyclical is True:
            tmpangle = polygonPoints[0] - polygonPoints[len(polygonPoints) - 1]
            slope = polygonPoints[0] - polygonPoints[len(polygonPoints) - 1]
            print(f"slope {tmpangle}")
            if tmpangle[1] == 0:
                tmpangle = 0
            elif tmpangle[0] == 0:
                tmpangle = np.pi / 2.0
            else:
                tmpangle = np.arctan(tmpangle[1] / tmpangle[0])
            # if slope[0] < 0:
            #     tmpangle += np.pi
            tmpangle = rotateIfLookingAway(slope, tmpangle)
            angles.append(tmpangle)
        angles = np.array(angles)
        print(f"Angles {angles*360/np.pi}")
        return angles

    def __str__(self):
        iscyc = ""
        if not self.cyclical:
            iscyc = "not "
        return f"Level with number {self.levelNumber} and {self.positions} positions that is {iscyc}cyclical. Points making the shape: {self.polygonPoints}, Enemy list: {self.enemyList}"


class Enemy(Player):
    def __init__(self, c, svgfile, spawndepth, spawnpos, color, lives):
        self.position = (
            spawnpos  # The game is effectively cyclical 2D as far as the position.
        )
        self.cycle = c  # It is cyclical but some levels arent so we will set negative values for noncyclical levels
        self.pointList = importPolygonFromSvg(svgfile)
        self.depth = spawndepth
        self.color = color
        self.tag = EntityTag.ENEMY
        self.lives = lives
        self.movementBuffer = 0
        self.shootBuffer = 0
        self.speed = 0.2

    def Shoot(self):
        return Projectile(
            self.position, self.depth + 1, 3, -1, (255, 0, 0), self.tag
        )

    def Behaviour(self, player, level, projectileList, randomness):
        distFromPlayer = player.position - self.position

        if distFromPlayer < 0:
            distFromPlayer = - abs(distFromPlayer) % len(level.positions)
        else:
            distFromPlayer = abs(distFromPlayer) % len(level.positions)

        # print(distFromPlayer)
        if distFromPlayer > 0:
            if level.checkIfOccupied(self.toCycle(self.position + 1)) == 0:
                self.movementBuffer += self.speed + rnd.randint(0, 10)/10.0 * randomness * self.speed

        if distFromPlayer < 0:
            if level.checkIfOccupied(self.toCycle(self.position - 1)) == 0:
                self.movementBuffer -= self.speed + rnd.randint(0, 10)/10.0 * randomness * self.speed

        if self.movementBuffer < -1:
            # level.updateOccupiedList(self.position, self.toCycle(self.position + 1))
            self.moveRight()
            self.movementBuffer = 0
            level.makeOccupiedList()

        if self.movementBuffer > 1:
            # level.updateOccupiedList(self.position, self.toCycle(self.position - 1))
            self.moveLeft()
            self.movementBuffer = 0
            level.makeOccupiedList()

        if level.checkIfOccupied(self.toCycle(self.position)) > 1:
            # level.updateOccupiedList(self.position, self.toCycle(self.position + 1))
            self.position = level.getEmptyPosition()
            level.makeOccupiedList()

        if player.position == self.position and self.shootBuffer < 0:
            ProjectileList[self.position].append(self.Shoot())
            pew_session.play()
            self.shootBuffer = 1
        else:
            self.shootBuffer -= 0.1

        # self.depth -= 0.1

    def __str__(self):
        iscyc = ""
        tmpcyc = self.cycle
        if self.cycle > 0:
            iscyc = "not "
        else:
            tmpcyc = tmpcyc * (-1)
        return f"Enemy in position {self.position} in level with {tmpcyc} positions that is {iscyc}cyclical. Points making the shape: {self.pointList}"


class Projectile:
    def __init__(self, spawnpos, spawndepth, length, speed, color, tag):
        self.position = spawnpos
        self.depth = spawndepth
        self.length = length
        self.speed = speed
        self.color = color
        self.tag = tag

    def moveProjectile(self):
        self.depth += self.speed


def getQuadFromSlope(slope):
    if slope[0] > 0 and slope[1] > 0:
        return Quadrant.FIRST
    elif slope[0] < 0 and slope[1] > 0:
        return Quadrant.SECOND
    elif slope[0] < 0 and slope[1] < 0:
        return Quadrant.THIRD
    elif slope[0] > 0 and slope[1] < 0:
        return Quadrant.FOURTH
    return Quadrant.FIRST


def getQuadFromAngle(angle):
    if angle >= 0 and angle <= np.pi/2:
        return Quadrant.FIRST
    elif angle > np.pi/2 and angle <= np.pi:
        return Quadrant.SECOND
    elif angle < 0 and angle >= - np.pi/2:
        return Quadrant.THIRD
    elif angle < - np.pi/2 and slope[1] >= - np.pi:
        return Quadrant.FOURTH
    return Quadrant.FIRST


def moveToQuad(angle, quad):                # unimplemented...
    tmpang = angle
    angQuad = getQuadFromAngle(angle)
    if angQuad!=quad:
        print("DIFFERENT")
    return tmpang


def rotateIfLookingAway(slope, angle):      # we attempted at solving a problem where the player won't face the right way we failed...
    newAngle = angle
    print(f"angle {angle/np.pi*360}")

    if getQuadFromAngle(angle)!=getQuadFromSlope(slope):
        print("DIFFERENT QUADS")
        # newAngle += np.pi

    if slope[0] < 0:
        newAngle += np.pi

    print(f"newAngle {newAngle/np.pi*360}")
    print()
    return newAngle


def scaleAgainstCenter(scale, polygonPoints, center):
    objectCenter = np.sum(polygonPoints, axis=0) / polygonPoints.shape[0]
    # print(f"center:  {objectCenter}")
    scaled = (polygonPoints - objectCenter) * scale + objectCenter
    scaled += center
    return scaled


# @jit
def drawLinesForLevel(polygonPoints, scaledPolygonPoints, screen, color, width):
    for i in range(polygonPoints.shape[0]):
        pygame.draw.line(screen, color, polygonPoints[i], scaledPolygonPoints[i], width)


def cameraPOVtransformation3D(cameraPos, polygonPoints, depth, d):
    newPoints = []
    output = []
    ddepth = depth
    if ddepth < 0:
        ddepth = (np.exp(ddepth) - 1) / (np.exp(ddepth) + 1)
    transformationMatrix = [[d, 0, 0, 0], [0, d, 0, 0], [0, 0, 0, 0], [0, 0, 1, d]]
    transformationMatrix = np.array(transformationMatrix)
    newPoints3D = []
    for i in polygonPoints:
        # print(f"i={i}")
        newPoints3D.append([i[0] + cameraPos[0], i[1] + cameraPos[1], i[2] + ddepth, 1])
    # print(f"newPoints3D{newPoints3D}")
    newPoints3D = np.array(newPoints3D)
    newPoints = np.matmul(newPoints3D, transformationMatrix)
    # print(f"newPoints{newPoints}")
    for i in newPoints:
        output.append(
            np.array([i[0] / (d + ddepth), i[1] / (d + i[2] + ddepth)]) * resolutionScale() * 2
            + resolution / 2.0
        )
    output = np.array(output)
    return output


# @jit
def cameraPOVtransformation(cameraPos, polygonPoints, depth, d):
    newPoints = []
    output = []
    ddepth = depth
    if ddepth < 0:
        ddepth = (np.exp(ddepth) - 1) / (np.exp(ddepth) + 1)
    # center = np.sum(polygonPoints, axis=0)/polygonPoints.shape[0]
    # print(f"center:{center}")
    for i in polygonPoints:
        newPoints.append(i + cameraPos)
    newPoints = np.array(newPoints)
    # print(f"polygon:{polygonPoints}")
    # print(f"newPoints:{newPoints.shape}")
    transformationMatrix = [[d, 0, 0, 0], [0, d, 0, 0], [0, 0, 0, 0], [0, 0, 1, d]]
    transformationMatrix = np.array(transformationMatrix)
    newPoints3D = []
    for i in newPoints:
        # print(f"i={i}")
        newPoints3D.append([i[0], i[1], ddepth, 1])
    # print(f"newPoints3D{newPoints3D}")
    newPoints3D = np.array(newPoints3D)
    newPoints = np.matmul(newPoints3D, transformationMatrix)
    # print(f"newPoints{newPoints}")
    for i in newPoints:
        output.append(
            np.array([i[0] / (d + ddepth), i[1] / (d + ddepth)]) * resolutionScale() * 2
            + resolution / 2.0
        )
    output = np.array(output)
    return output


# @jit
def resolutionScale():
    if resolution[0] > resolution[1]:
        return resolution[1] / resolution[0]
    return resolution[0] / resolution[1]


# @jit
def accelerateCam(player, level, cameraPos, velocity):
    cameraP = cameraPos
    ppos = level.positions[player.position]
    center = np.sum(level.polygonPoints, axis=0) / level.polygonPoints.shape[0]
    cameraWish = (center - ppos) / (2) - cameraP
    if 0 != cameraWish[0] or 0 != cameraWish[1]:
        cameraP = cameraP + (cameraWish) * velocity
    return cameraP


def DrawGame(player, level, screen, cameraP, projList, zoom):
    ppos = level.localToLevelSpace(player.position, player.pointList)

    scaled = cameraPOVtransformation(
        cameraPos, level.polygonPoints, playDepth + zoom, 1
    )
    front = cameraPOVtransformation(cameraPos, level.polygonPoints, zoom, 1)
    ppos = cameraPOVtransformation(cameraPos, ppos, player.depth, 1)

    for j in projList:
        for i in j:
            point1 = cameraPOVtransformation(
                cameraPos, np.array([level.positions[i.position]]), i.depth, 1
            )
            point2 = cameraPOVtransformation(
                cameraPos, np.array([level.positions[i.position]]), i.depth + i.length, 1
            )
            point1 = point1[0]
            point2 = point2[0]
            pygame.draw.line(screen, i.color, point1, point2)
    pygame.draw.polygon(screen, level.color, front, 1)
    pygame.draw.polygon(screen, level.color, scaled, 1)
    drawLinesForLevel(front, scaled, screen, level.color, 1)
    for enemy in level.enemyList:
        ipos = level.localToLevelSpace(enemy.position, enemy.pointList)
        ipos = cameraPOVtransformation(cameraPos, ipos, enemy.depth, 1)
        pygame.draw.polygon(screen, enemy.color, ipos, 1)
    if playMode != PlayMode.CHANGELEVEL:
        pygame.draw.polygon(screen, player.color, ppos, 1)


def MoveToResolution(points, offset):
    output = []
    for i in points:
        output.append(np.array(i) + resolution / 2 + offset)

    return np.array(output)




def DrawMainMenu(screen):
    font = pygame.font.Font("freesansbold.ttf", 32)


    # create a text surface object,
    # on which text is drawn on it.
    text = font.render("Main Menu", True, (0, 255, 0))
    text2 = font.render("Press Enter To Start Game Or Esc To Exit", True, (0, 255, 0))

    # create a rectangular object for the
    # text surface object
    textRect = text.get_rect()
    textRect2 = text2.get_rect()

    # set the center of the rectangular object.
    textRect.center = resolution / 2 + np.array([-30, -320])
    textRect2.center = resolution / 2 + np.array([-25, 300])

    screen.blit(text, textRect)
    screen.blit(text2, textRect2)

    pygame.draw.polygon(
        screen, (255, 255, 255), MoveToResolution(logo, np.array([-30, 250])), 1
    )


def DrawPauseMenu(screen):
    font = pygame.font.Font("freesansbold.ttf", 32)

    text = font.render("Game Paused", True, (0, 255, 0))
    text2 = font.render("Press Q To Exit Game Or Esc To Resume Game", True, (0, 255, 0))

    textRect = text.get_rect()
    textRect2 = text2.get_rect()

    textRect.center = resolution / 2 + np.array([-25, -320])
    textRect2.center = resolution / 2 + np.array([-15, 300])

    screen.blit(text, textRect)
    screen.blit(text2, textRect2)


def DrawStars(screen):
    starDepth = 0
    starDepthEnd = -20
    starNumber = 1
    starPoints = []
    for i in range(starNumber):
        posi = rnd.randint(-200, 200)
        starPoints.append([rnd.randint(-200, 200), rnd.randint(-200, 200), rnd.randint(0, 20)])
    starPoints = np.array(starPoints)
    while starDepth > starDepthEnd:
        points = cameraPOVtransformation3D(np.array([0,0]), starPoints, starDepth, 1)
        print(f"drawing stars with depth {starDepth}")
        starDepth -= 0.01
        i = 0
        while i < len(points) - 1:
            pygame.draw.line(screen, (255, 255 , 255), points[i], points[i+1])
            i += 1
        pygame.display.flip()


def DrawWin(screen):
    font = pygame.font.Font("freesansbold.ttf", 32)

    win_text = font.render("Congratulations You Win!!", True, (0, 255, 0))

    textRect = win_text.get_rect()

    textRect.center = resolution / 2 + np.array([-30, -320])

    screen.blit(win_text, textRect)

    pygame.display.flip()
    time.sleep(3)



def DrawLoss(screen):
    font = pygame.font.Font("freesansbold.ttf", 32)

    game_over_text = font.render("Game Over", True, (255, 0, 0))

    textRect = game_over_text.get_rect()

    textRect.center = resolution / 2 + np.array([-30, -320])

    screen.blit(game_over_text, textRect)
    death_session.play()
    pygame.display.flip()
    time.sleep(3)


def DrawHUD(screen, player, levelcount):

    font = pygame.font.Font("freesansbold.ttf", 32)
    text = font.render(f"Level: {levelCount+1}", True, (0, 255, 0))
    textRect = text.get_rect()
    textRect.center = resolution / 2 + np.array([-570, -320])
    screen.blit(text, textRect)

    textRect = text.get_rect()

    for i in range(player.lives):
        pygame.draw.polygon(
            screen,
            (255, 0, 0),
            MoveToResolution(heart, np.array([500 + i * 50, -320])),
            1,
        )


ProjectileList = []
LevelList = []

#Level 1
LevelList.append(Level(1, [], "Level1.svg", (0, 0, 255), 3))    ####### eixame 5 anti gia 3
for enm in range(3):
    LevelList[0].enemyList.append(
        Enemy(
            LevelList[0].getCyclicalForPlayer(),
            "Enemy_Low.svg",
            playDepth,
            0,
            (255, 0, 0),
            1,
        )
    )

#Level 2
LevelList.append(Level(2, [],"Level2.svg", (0, 0, 255), 4))
for enm in range(3):
    LevelList[1].enemyList.append(
        Enemy(
            LevelList[1].getCyclicalForPlayer(),
            "Enemy_Low.svg",
            playDepth,
            0,
            (255, 0, 0),
            1,
        )
    )
for enm in range(1):
    LevelList[1].enemyList.append(
        Enemy(
            LevelList[1].getCyclicalForPlayer(),
            "Enemy_Medium.svg",
            playDepth,
            0,
            (255, 0, 0),
            2,
        )
    )

#Level 3
LevelList.append(Level(3, [],"Level3.svg", (0, 0, 255), 5))
for enm in range(5):
    LevelList[2].enemyList.append(
        Enemy(
            LevelList[2].getCyclicalForPlayer(),
            "Enemy_Medium.svg",
            playDepth,
            0,
            (255, 0, 0),
            3,
        )
    )

#Level 4
LevelList.append(Level(4, [],"Level4.svg", (0, 0, 255), 6))
for enm in range(3):
    LevelList[3].enemyList.append(
        Enemy(
            LevelList[3].getCyclicalForPlayer(),
            "Enemy_Low.svg",
            playDepth,
            0,
            (255, 0, 0),
            2,
        )
    )
for enm in range(3):
    LevelList[3].enemyList.append(
        Enemy(
            LevelList[3].getCyclicalForPlayer(),
            "Enemy_Medium.svg",
            playDepth,
            0,
            (255, 0, 0),
            3,
        )
    )

#Level 5
LevelList.append(Level(5, [],"Level5.svg", (0, 0, 255), 7))
for enm in range(6):
    LevelList[4].enemyList.append(
        Enemy(
            LevelList[4].getCyclicalForPlayer(),
            "Enemy_Medium.svg",
            playDepth,
            0,
            (255, 0, 0),
            3,
        )
    )
for enm in range(1):
    LevelList[4].enemyList.append(
        Enemy(
            LevelList[4].getCyclicalForPlayer(),
            "Enemy_High.svg",
            playDepth,
            0,
            (255, 0, 0),
            5,
        )
    )

#Level 6
LevelList.append(Level(6, [],"Level6.svg", (0, 0, 255), 8))

for enm in range(3):
    LevelList[5].enemyList.append(
        Enemy(
            LevelList[5].getCyclicalForPlayer(),
            "Enemy_Low.svg",
            playDepth,
            0,
            (255, 0, 0),
            2,
        )
    )

for enm in range(3):
    LevelList[5].enemyList.append(
        Enemy(
            LevelList[5].getCyclicalForPlayer(),
            "Enemy_Medium.svg",
            playDepth,
            0,
            (255, 0, 0),
            3,
        )
    )
for enm in range(2):
    LevelList[5].enemyList.append(
        Enemy(
            LevelList[5].getCyclicalForPlayer(),
            "Enemy_High.svg",
            playDepth,
            0,
            (255, 0, 0),
            5,
        )
    )

for lvl in LevelList:
    lvl.makeOccupiedList()

BaseLevel = copy.deepcopy(LevelList[0])
BasePlayer = Player(BaseLevel.getCyclicalForPlayer(), "Player.svg", (0, 255, 0), 3)

for i in range(len(BaseLevel.positions)):
    ProjectileList.append([])
# print(f"pjlist{ProjectileList}")

# print(BaseLevel)
# print(BasePlayer)


screen = pygame.display.set_mode(resolution, pygame.RESIZABLE)  # Set Resolution
pygame.display.set_caption("Another Tempest Clone")  # Sets Name For The Game
clock = pygame.time.Clock()  # Object To Control The Framerate

BaseSurface = pygame.Surface(resolution)
screen.fill("black")
cameraPos = np.array([0, 0])
wishVector = 0
shootVector = 0
zoom = startZoom
levelCount = 0
t = 0
pauseBuffer = 0
pauseBufferDiff = 0
prevPauseBuffer = 0



tmpPmode = playMode

while True:
    # print(f"{playMode} {levelCount}")
    prevPauseBuffer = pauseBuffer
    for event in pygame.event.get():  # Checks for Events From Keyboard Or Mouse
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    # print(zoom)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        pauseBuffer = 1
        
    else:
        pauseBuffer = 0
    pauseBufferDiff = pauseBuffer - prevPauseBuffer


    if zoom > 0:
        zoom -= zoomSpeed
        BasePlayer.depth = zoom

    if playMode == PlayMode.PAUSE:

        if keys[pygame.K_q]:
            pygame.quit()
            exit()

        if pauseBufferDiff == 1:
            playMode = PlayMode.PLAY
            pauseBufferDiff = 0

    if playMode == PlayMode.PLAY:

        if pauseBufferDiff == 1:
            playMode = PlayMode.PAUSE
            pause_session.play()
            pauseBufferDiff = 0

        if keys[pygame.K_LEFT]:
            wishVector -= sensitivity
        if keys[pygame.K_RIGHT]:
            wishVector += sensitivity
        if keys[pygame.K_SPACE] and shootVector <= 0:
            ProjectileList[BasePlayer.position].append(BasePlayer.Shoot())
            shootVector = 1
            shoot_effect.play()

    if playMode == PlayMode.DEMO:

        if keys[pygame.K_RETURN]:
            playMode = PlayMode.PLAY
            zoom = startZoom
            levelCount = 0
            BaseLevel = copy.deepcopy(LevelList[levelCount])
            BasePlayer = Player(BaseLevel.getCyclicalForPlayer(), "Player.svg", (0, 255, 0), 3)
            ProjectileList = []
            for i in range(len(BaseLevel.positions)):
                ProjectileList.append([])
            # print(f"pjlist{ProjectileList}")
        if pauseBuffer == 1:
            pygame.quit()
            exit()

        if rnd.randint(0, 1) > 0:
            wishVector -= sensitivity
        if rnd.randint(0, 1) > 0:
            wishVector += sensitivity
        if rnd.randint(0, 1) > 0 and shootVector <= 0:

            ProjectileList[BasePlayer.position].append(BasePlayer.Shoot())
            # print(f"baseplayerpos{BasePlayer.position} and object {ProjectileList[BasePlayer.position]}")
            # print("Shoot")
            shootVector = 1
            shoot_effect.play()

    if wishVector < -1:
        BasePlayer.moveLeft()
        wishVector = 0
    if wishVector > 1:
        BasePlayer.moveRight()
        wishVector = 0
    if shootVector > 0:
        shootVector -= shootCooldown

    if playMode == PlayMode.CHANGELEVEL:
        # DrawStars(screen)
        if levelCount > len(LevelList) - 2:
            playMode = PlayMode.DEMO
            BaseLevel = copy.deepcopy(LevelList[0])
            levelCount = -1
            for i in range(len(BaseLevel.positions)):
                ProjectileList.append([])
            # print(f"pjlist{ProjectileList}")
            BasePlayer = Player(BaseLevel.getCyclicalForPlayer(), "Player.svg", (0, 255, 0), 3)
            DrawWin(screen)
        else:
            levelCount += 1
            BasePlayer.position = 0
            BaseLevel = copy.deepcopy(LevelList[levelCount])
            BasePlayer.cycle = BaseLevel.getCyclicalForPlayer()
            ProjectileList = []
            for i in range(len(BaseLevel.positions)):
                ProjectileList.append([])
            playMode = tmpPmode
            zoom = startZoom

    if playMode != PlayMode.PAUSE and playMode != PlayMode.CHANGELEVEL:
        i = 0
        while i < len(ProjectileList[BasePlayer.position]):
            if ProjectileList[BasePlayer.position][i].depth < 0 and ProjectileList[BasePlayer.position][i].tag != BasePlayer.tag and not invinsible:
                popped = ProjectileList[BasePlayer.position].pop(i)
                i -= 1
                BasePlayer.lives -= 1
                # print(f"baseplayer lives {BasePlayer.lives}")
            i += 1
        i = 0
        while i < len(ProjectileList):
            j = 0
            # print(ProjectileList[i])
            while j < len(ProjectileList[i]):
                ProjectileList[i][j].moveProjectile()
                if ProjectileList[i][j].depth > playDepth or ProjectileList[i][j].depth < -1:
                    popped = ProjectileList[i].pop(j)
                    # print(f"popped{popped}")
                    j -= 1
                j += 1
            i += 1
        if BasePlayer.lives < 1:
            if playMode == PlayMode.PLAY:
                DrawLoss(screen)
            playMode = PlayMode.DEMO
            BaseLevel = copy.deepcopy(LevelList[0])
            levelCount = 0
            for i in range(len(BaseLevel.positions)):
                ProjectileList.append([])
            # print(f"pjlist{ProjectileList}")
            BasePlayer = Player(BaseLevel.getCyclicalForPlayer(), "Player.svg", (0, 255, 0), 3)
            zoom = startZoom
        if len(BaseLevel.enemyList) < 1 and zoom >= endZoom:
            zoom -= zoomSpeed
            t = 0
        if zoom < endZoom:
            tmpPmode = playMode
            playMode = PlayMode.CHANGELEVEL

        if zoom <= 0:
            en = 0
            while en < min(len(BaseLevel.enemyList), BaseLevel.concurrentEnemies):
                BaseLevel.enemyList[en].Behaviour(BasePlayer, BaseLevel, ProjectileList, 1)
                proj = 0
                allproj = len(ProjectileList[BaseLevel.enemyList[en].position])
                while proj < allproj:
                    if BaseLevel.enemyList[en].depth > ProjectileList[BaseLevel.enemyList[en].position][proj].depth and ProjectileList[BaseLevel.enemyList[en].position][proj].tag == BasePlayer.tag:
                        BaseLevel.enemyList[en].lives -= 1
                        ProjectileList[BaseLevel.enemyList[en].position].pop(proj)
                        proj -= 1
                        allproj -= 1
                    proj += 1
                if BaseLevel.enemyList[en].lives < 1:
                    BaseLevel.enemyList.pop(en)
                    BaseLevel.makeOccupiedList()
                    en -= 1
                en += 1
    # print(ProjectileList)



    screen.fill("black")
    cameraPos = accelerateCam(BasePlayer, BaseLevel, cameraPos, cameraSpeed)
    DrawGame(BasePlayer, BaseLevel, screen, cameraPos, ProjectileList, zoom)
    DrawHUD(screen, BasePlayer, levelCount)
    if playMode == PlayMode.PAUSE:
        DrawPauseMenu(screen)
    if playMode == PlayMode.DEMO:
        DrawMainMenu(screen)
    pygame.display.flip()
    # pygame.display.update()
    resolution = np.array(pygame.display.get_window_size())
    deltaTime = clock.tick(60)  # 60 Frames/Second
