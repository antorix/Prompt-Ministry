#!/usr/bin/python
# -*- coding: utf-8 -*-
Simplified=0

import sys
import os
import time
import datetime
import json
import urllib.request

def initializeDB():
    """ Возвращает изначальное значение houses, settings, resources как при создании базы заново"""

    return [],\
        [
        [1, 0, 0, 0, "с", 0, 50, 1, 1, 0, 1, 0, 1, "#", "", 1, 0, "", 1, "д", 1, 0, 1], # program settings: settings[0][0…], see set.preferences()
        "",  # не используется!         settings[1]
        # report:                       settings[2]
        [0.0,       # [0] hours         settings[2][0…]
         0.0,       # [1] credit
         0,         # [2] placements
         0,         # [3] videos
         0,         # [4] returns,
         0,         # [5] studies,
         0,         # [6] startTime
         0,         # [7] endTime
         0.0,       # [8] reportTime
         0.0,       # [9] difTime
         "",        # [10] note
         0,         # [11] to remind submit report (0: already submitted)
         ""         # [12] отчет прошлого месяца
         ],
        time.strftime("%b", time.localtime()),  # month of last save: settings[3]
        [None, None, None, None, None, None, None, None, None, None, None, None] # service year: settings[4]
    ],\
        [
            [],     # notebook              resources[0]
            [],     # standalone contacts   resources[1]
            []      # report log             resources[2]
    ]

houses, settings, resources = initializeDB()
DBCreatedTime = ""
Version = "0.7.0"

"""
# Изменения новой версии:
* Четыре типа участков: многоквартирный дом, деловая территория, частный сектор, список телефонных номеров
* В отчете можно создать примечание
* Консольный режим для стандартного Python без графики (по умолчанию отключен в настройках)
* Функция определения статуса квартиры с помощью цифры в конце строки посещения (по умолчанию отключена)
* Автоматическое обновление программы в фоновом режиме
* Мелкие интерфейсные изменения
"""

try: # определяем ОС
    print("Загружаем графическую библиотеку")
    time.sleep(0.2)
    from androidhelper import Android
except:
    try:
        import easygui_mod
    except:
        Mode = "text"
        UserPath = ""
        BackupFolderLocation = "./backup/"
        print("Графическая библиотека не найдена, входим в консольный режим")
    else:
        Mode = "easygui"
        UserPath = ""
        BackupFolderLocation = "./backup/"
else:
    Mode = "sl4a"
    phone = Android()
    UserPath = phone.environment()[1]["download"][:phone.environment()[1]["download"].index("/Download")]\
                      + "/qpython/projects3/RocketMinistry/" # check location of PM folder    
    BackupFolderLocation = UserPath + "backup/"
    AndroidDownloadPath = Android().environment()[1]["download"] + "/"

from house_op import addHouse

LastTimeDidChecks = LastTimeBackedUp = int(time.strftime("%H", time.localtime())) * 3600 \
                + int(time.strftime("%M", time.localtime())) * 60 \
                + int(time.strftime("%S", time.localtime()))

def log(message):
    """ Displaying and logging to file important system messages """

    if Mode == "sl4a":
        phone.makeToast(message)
    else:
        print("%s" % message)
        if settings[0][1]==True or "--textconsole" in sys.argv:
            time.sleep(0.5)

def clearDB():
    """ Очистка базы данных """
    houses.clear()
    settings.clear()
    resources.clear()
    settings[:] = initializeDB()[1][:]
    resources[:] = initializeDB()[2][:]
    if os.path.exists(UserPath + "data.jsn"):
        os.remove(UserPath + "data.jsn")
    if os.path.exists(UserPath + 'backup'):
        from shutil import rmtree
        rmtree(UserPath + 'backup')

def getDBCreatedTime(dataFile="data.jsn"):
    """ Выдает время последнего изменения базы данных, но не в упрощенном режиме """
    if Simplified==True:
        return ""
    try:
        if Mode=="sl4a" and os.path.exists(UserPath + dataFile):
            DBCreatedTime = datetime.datetime.fromtimestamp(os.path.getmtime(UserPath + dataFile))
        elif os.path.exists(dataFile):
            DBCreatedTime = datetime.datetime.fromtimestamp(os.path.getmtime(dataFile))
        else:
            DBCreatedTime = "(Не удалось получить время базы данных)"
        return "(сохр. {:%d.%m %H:%M})".format(DBCreatedTime)
    except:
        return "(отсутствует)"

def load(dataFile="data.jsn", download=False, clipboard=False, forced=False, delete=False):
    """ Loading houses and settings from JSON file """

    print("Загружаем базу данных")

    buffer=[]

    if Mode == "sl4a":
        if download == True: # загрузка файла из папки загрузок телефона
            if os.path.exists(AndroidDownloadPath + dataFile):
                with open(AndroidDownloadPath + dataFile, "r") as file:
                    buffer = json.load(file)
                if delete==True:
                    os.remove(AndroidDownloadPath + dataFile) # файл удаляется, чтобы при последующем сохранении на телефоне у него не изменилось название

        elif os.path.exists(UserPath + dataFile): # обычная загрузка
            with open(UserPath + dataFile, "r") as file:
                buffer = json.load(file)

    else:
        if clipboard == True: # вставляем базу данных из буфера обмена
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                buffer = json.loads(win32clipboard.GetClipboardData())
                win32clipboard.CloseClipboard()
            except:
                log("Ошибка импорта!")
                return

        else: # обычная загрузка, файла по умолчанию или через импорт
            if forced==True and not os.path.exists(dataFile):
                from dialogs import dialogFileOpen
                choice = dialogFileOpen(default=settings[0][14])
                if choice == None or choice==".":
                    return
                else:
                    settings[0][14] = choice.strip()
                    dataFile = settings[0][14]
                    save()
            if forced==False and not os.path.exists(dataFile):
                print("База не найдена, начинаем заново")
            try:
                with open(dataFile, "r") as file:
                    buffer = json.load(file)
                #if delete==True:
                #    os.remove(dataFile) # файл удаляется, поскольку с телефона может не получиться перезаписать существующий файл
            except:
                if forced==True:
                    from dialogs import dialogInfo
                    dialogInfo(title="Загрузка базы данных",
                               message="Файл базы данных не найден или поврежден! Проверьте путь файла и попробуйте еще раз."
                    )
                return

    if len(buffer)==0:
        if forced == True:
            from dialogs import dialogInfo
            dialogInfo(title="Загрузка данных", message="Файл не найден!")
        else:
            pass

    elif len(buffer)>0: # буфер получен, читаем из него
        if forced==True: # при импорте из интерфейса программы сначала нужно очистить базу
            clearDB()

        if buffer[0] == "Rocket Ministry application data file. Format: JSON. Do NOT edit manually!":
            del buffer[0]
            settings[4] = buffer[0][4]
        else:
            settings[4] = [None, None, None, None, None, None, None, None, None, None, None, None, None]
        settings[0] = buffer[0][0]
        settings[1] = buffer[0][1]
        settings[2] = buffer[0][2]
        settings[3] = buffer[0][3]

        #if len(settings[0])<23:
        #    settings[0].append(1) # добавление новых настроек для тех пользователей, у которых их нет

        resources[0] = buffer[1][0]  # загружаем блокнот

        resources[1] = []  # загружаем отдельные контакты
        virHousesNumber = int(len(buffer[1][1]))
        hr = []
        for s in range(virHousesNumber):
            hr.append(buffer[1][1][s])  # creating temporary string houses, one string per house
        houseRetrieve(resources[1], virHousesNumber, hr, silent=True)

        resources[2] = buffer[1][2] # загружаем журнал отчета

        housesNumber = int(len(buffer)) - 2 # загружаем обычные дома
        h = []
        for s in range(2, housesNumber + 2):
            h.append(buffer[s])  # creating temporary string houses, one string per house
        houseRetrieve(houses, housesNumber, h, silent=True)

    #except:
    #    return # не удалось загрузить данные, выходим и оставляем чистую базу
    #else:
        if forced == True:
            log("База успешно загружена")

def houseRetrieve(containers, housesNumber, h, silent=False):
    """ Retrieves houses from JSON buffer into objects """

    for a in range(housesNumber):

        addHouse(containers, h[a][0], h[a][4], save=False)  # creating house and writing its title and type
        containers[a].porchesLayout = h[a][1]
        containers[a].date = h[a][2]
        containers[a].note = h[a][3]

        porchesNumber = len(h[a][5])  # counting porches
        for b in range(porchesNumber):
            containers[a].addPorch(h[a][5][b][0], save=False)  # creating porch and writing its title and layout
            containers[a].porches[b].status = h[a][5][b][1]
            containers[a].porches[b].flatsLayout = h[a][5][b][2]
            containers[a].porches[b].floor1 = h[a][5][b][3]
            containers[a].porches[b].note = h[a][5][b][4]
            containers[a].porches[b].type = h[a][5][b][5]

            flatsNumber = len(h[a][5][b][6])  # counting flats
            for c in range(flatsNumber):
                containers[a].porches[b].addFlat("+" + h[a][5][b][6][c][0], silent=True, save=False, forceStatusUpdate=True)  # creating flat and writing its title
                containers[a].porches[b].flats[c].note = h[a][5][b][6][c][1]
                containers[a].porches[b].flats[c].number = h[a][5][b][6][c][2]
                containers[a].porches[b].flats[c].status = h[a][5][b][6][c][3]
                containers[a].porches[b].flats[c].phone = h[a][5][b][6][c][4]
                containers[a].porches[b].flats[c].meeting = h[a][5][b][6][c][5]

                visitNumber = len(h[a][5][b][6][c][6])  # counting visits
                for d in range(visitNumber):
                    containers[a].porches[b].flats[c].addRecord(
                        h[a][5][b][6][c][6][d][1], save=False, forceStatusUpdate=True)  # creating visit and writing its title
                    containers[a].porches[b].flats[c].records[d].date = h[a][5][b][6][c][6][d][
                        0]  # rewriting date to original

def save(forced=False):
    """ Saving database to JSON file """

    global LastTimeBackedUp

    # Выгружаем все данные в список

    output = ["Rocket Ministry application data file. Format: JSON. Do NOT edit manually!"] + [settings] + \
             [[resources[0], [resources[1][i].export() for i in range(len(resources[1]))], resources[2]]]
    for i in range(len(houses)):
        output.append(houses[i].export())

    # Сначала резервируем раз в 5 минут

    curTime = int(time.strftime("%H", time.localtime())) * 3600 \
              + int(time.strftime("%M", time.localtime())) * 60 \
              + int(time.strftime("%S", time.localtime()))
    if forced==True or (settings[0][6] > 0 and (curTime - LastTimeBackedUp) > 300):
        if not os.path.exists(BackupFolderLocation):
            try:
                os.makedirs(BackupFolderLocation)
            except IOError:
                log("Не удалось создать резервную копию!")
                return
        savedTime = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
        with open(BackupFolderLocation + "data_" + savedTime + ".jsn", "w") as newbkfile:
            json.dump(output, newbkfile)
            if forced == True:
                log("Создана резервная копия")
            LastTimeBackedUp = curTime

    # Сохраняем

    try:
        with open(UserPath + "data.jsn", "w") as file:
            json.dump(output, file)
    except IOError:
        log("Не удалось сохранить базу!")
    else:
        if forced == True:
            log("База успешно сохранена")

def share(outside=False):
    """ Sharing database """
    
    output = ["Rocket Ministry application data file. Format: JSON. Do NOT edit manually!"] + [settings] +\
             [[resources[0], [ resources[1][i].export() for i in range(len(resources[1])) ] ]]
    for i in range(len(houses)):
        output.append(houses[i].export())
    
    buffer = json.dumps(output)    
    
    if Mode == "sl4a": # Sharing to cloud if on Android
        try:
            phone.sendEmail("Введите email","data.jsn",buffer,attachmentUri=None)
        except IOError:
            log("Не удалось отправить базу!")
        else:
            if outside==False:
                consoleReturn()
            else:
                log("Выгрузка базы данных")
    else:
        from webbrowser import open
        open("data.jsn")

def backupRestore(restore=False, delete=False, silent=False):
    """ Восстановление файла из резервной копии """

    from dialogs import dialogInfo
    if os.path.exists(BackupFolderLocation)==False:
        if silent == False:
            dialogInfo(title="Восстановление", message="Папки резервных файлов не существует!")
        return
    files = [f for f in os.listdir(BackupFolderLocation) if os.path.isfile(os.path.join(BackupFolderLocation, f))]
    fileDates = []
    for i in range(len(files)):
        fileDates.append(str("{:%d.%m.%Y, %H:%M:%S}".format(
            datetime.datetime.strptime(time.ctime((os.path.getmtime(BackupFolderLocation + files[i]))),
                                       "%a %b %d %H:%M:%S %Y"))))

    # Если выбран режим восстановления

    if restore == True:
        from dialogs import dialogList
        from icons import icon
        choice2 = dialogList(
            title=icon(
                "restore") + " Восстановление",
            message="Выберите дату и время резервной копии базы данных, которую нужно восстановить:",
            options=fileDates,
            form="restore"
        )  # choose file

        if choice2 == None:
            return
        elif choice2 == "":
            if settings[0][1] == True:
                return
        else:
            del houses[:]
            try:
                load(dataFile="backup/" + files[int(choice2)])  # load from backup copy
            except:
                log("Не удалось восстановить данные!")
            else:
                log("Данные успешно восстановлены из файла " + BackupFolderLocation + files[choice2])

    # Если выбран режим удаления лишних файлов

    elif delete == True:
        print("Проверяем лишние резервные копии")
        limit = settings[0][6]
        if len(files) > limit:  # лимит превышен, удаляем
            extra = len(files) - limit
            for i in range(extra):
                os.remove(BackupFolderLocation + files[i])

def update():
    """ Проверяем новую версию и при наличии обновляем программу с GitHub """

    print("Проверяем обновления")
    for line in urllib.request.urlopen("https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/version"):
        version = line.decode('utf-8')

    curVersion = [int(Version[0]), int(Version[2]), int(Version[4])]
    newVersion = [int(version[0]), int(version[2]), int(version[4])]
    if newVersion > curVersion:
        print("Найдена новая версия!")
        """
        urls = ["https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/console.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/contacts.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/dialogs.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/homepage.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/house_cl.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/house_op.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/icons.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/io2.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/main.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/notebook.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/reports.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/set.py",
                "https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/territory.py"
                ]
        if Mode=="easy_gui":
            urls.append("https://raw.githubusercontent.com/antorix/Rocket-Ministry/master/easy_gui.py")    
        for url in urls:
            urllib.request.urlretrieve(url, UserPath + url[url.index("master/") + 7:])
        """

def consoleReturn():
    os.system("clear")
    input("\nНажмите Enter для возврата")
    os.system("clear")