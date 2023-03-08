from PIL import Image, ImageFont, ImageDraw
from alive_progress import alive_bar
import imageio.v2 as imageio
import threading
import datetime
import shutil
import time
import cv2
import os

asciiChars = ["@", "#", "$", "%", "?", "*", "+", ";", ":", ",", ".", "!", "^", "&", "(", ")", "'", "[", "]", "{", "}", "\\", "/", "<", ">", "|", "=", "_", "-"]


def resizedGreyImage(image):
    newWidth=300

    width, height = image.size
    aspectRatio = height / width

    newHeight = int(aspectRatio * newWidth)

    resizedGreyImage = image.resize((newWidth, newHeight)).convert('L')

    return resizedGreyImage


def pixToChars(image):
    pixels = image.getdata()
    characters = "".join([asciiChars[pixel//25] for pixel in pixels])
    
    return characters


def generateFrame(image):
    newWidth = 300

    newImageData = pixToChars(resizedGreyImage(image))
    
    totalPixels = len(newImageData)

    asciiImage = "\n".join([newImageData[index:(index+newWidth)] for index in range(0, totalPixels, newWidth)])

    return asciiImage


def generateAsciiFrames(totalFrameCount, videoFrameList):
    print("Generating ASCII Frames...")

    textFrameList = []

    with alive_bar(totalFrameCount) as bar:
        for frame in videoFrameList:
            textFrameList.append(generateFrame(Image.fromarray(frame)))
            bar()
    
    return textFrameList


class ConvertAsciiFrames():
    def handler(videoPath, totalFrameCount, textFrameList):
        print("Converting ASCII Frames to PNG Files...")  

        pngFilesPath, frameDirPath = ConvertAsciiFrames.createPngPath(videoPath)

        threadCount = os.cpu_count()
        distributionArray = {}

        for i in range(threadCount):
            distributionArray[i+1] = []

        counter = 1
        for i in range(totalFrameCount):
            distributionArray[counter].append((textFrameList[i], i+1))
            
            if counter == threadCount:
                counter = 1
            else:
                counter += 1

        threads = []
        with alive_bar(totalFrameCount) as bar:
            for i in range(threadCount):
                thread = threading.Thread(target=ConvertAsciiFrames.textFrameToPngConverter, args=(distributionArray[i+1], pngFilesPath, bar,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

        return pngFilesPath, frameDirPath

    
    def textFrameToPngConverter(frameList, pngFilesPath, bar):
        for item in frameList:
            frame = item[0]
            frameNum = item[1]

            newPngFrame = image = Image.new("RGB", (int(720*2.54), int(1280*6.27)))

            image = ImageDraw.Draw(newPngFrame)
            image.text((15,15), frame, (237, 230, 211), font=ImageFont.load_default())
            newPngFrame.save(f"{pngFilesPath}\\frame{frameNum}.png")

            bar()
        
        return


    def createPngPath(videoPath):
        frameDirPath = os.path.splitext(videoPath)[0]
        frameDirPath += "_ASCII"
        if not os.path.isdir(frameDirPath):
            os.makedirs(f"{frameDirPath}")

        pngFilesPath = f"{frameDirPath}"

        return pngFilesPath, frameDirPath
    

class PngToGifConverter():
    def handler(totalFrameCount, pngFilesPath, frameDirPath):
        print("Constructing GIF Components From PNG Files...")
            
        pngFrames = PngToGifConverter.componentConstructor(totalFrameCount, pngFilesPath)

        print()
        print("Writing Constructed GIF Components to GIF File...")

        PngToGifConverter.componentCombiner(totalFrameCount, frameDirPath, pngFrames)

        return


    def componentConstructor(totalFrameCount, pngFilesPath):
        pngFrames = []

        with alive_bar(totalFrameCount) as bar:
            for i in range(totalFrameCount):
                pngFrames.append(imageio.imread(f"{pngFilesPath}\\frame{i+1}.png"))

                bar()

        return pngFrames

    def componentCombiner(totalFrameCount, frameDirPath, pngFrames):
        with alive_bar(totalFrameCount) as bar:
            with imageio.get_writer(f"{frameDirPath}.gif", mode='I') as writer:
                for pngData in pngFrames:
                    writer.append_data(pngData)

                    bar()

        return


if __name__ == "__main__":
    while True:
        videoPath = input("Enter Video: ")

        if os.path.isfile(videoPath):
            break
        else:
            print("Video not found.")
            print()

    os.system('cls')

    timeStart = time.time()

    capture = cv2.VideoCapture(videoPath)

    print("Counting Frames in Video...")

    frameExist = True
    totalFrameCount = -1
    videoFrameList = []

    while frameExist:
        totalFrameCount += 1
        frameExist, frame = capture.read()
        videoFrameList.append(frame)

    videoFrameList.pop(len(videoFrameList)-1)

    print(f"Frame Count: {totalFrameCount}")
    print()

    capture = cv2.VideoCapture(videoPath)

    textFrameList = generateAsciiFrames(totalFrameCount, videoFrameList)

    print()

    pngFilesPath, frameDirPath = ConvertAsciiFrames.handler(videoPath, totalFrameCount, textFrameList)

    print()

    PngToGifConverter.handler(totalFrameCount, pngFilesPath, frameDirPath)

    shutil.rmtree(pngFilesPath)

    secondsTook = time.time() - timeStart

    milliseconds = str(secondsTook-int(secondsTook)).split('.')[1]
    milliseconds = milliseconds[0:3]

    timeTook = str(datetime.timedelta(seconds=int(secondsTook)))

    timeTookSeconds = timeTook[5:7]
    timeTookMinutes = timeTook[2:4]
    timeTookHours = timeTook[0]

    print()
    print("Completed Generating ASCII GIF.")
    print()
    print(f"Took: {timeTookHours}h {timeTookMinutes}m {timeTookSeconds}s {milliseconds}ms")
    print()

    input("Press ENTER Key to Exit...")
    exit()