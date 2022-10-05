#!/usr/bin/python
# -*- coding: utf-8 -*-

import io2
from io2 import houses
from io2 import settings
from io2 import resources
import territory
import contacts
import dialogs
import reports
import set
import notebook
import house_op
import time
from icons import icon

def homepage():
    """ Home page """

    #territory.porchView(houses[3], 0)

    #if "--textmode" in sys.argv:  # проверяем параметры командной строки
    #    settings[0][1] = 1

    while 1:

        appointment = "" # поиск контактов со встречей на сегодня
        totalContacts, datedFlats = contacts.getContactsAmount(date=1)
        if len(datedFlats)>0:
            appointment = icon("appointment")

        curTime = int(time.strftime("%H", time.localtime())) * 3600 \
                  + int(time.strftime("%M", time.localtime())) * 60 \
                  + int(time.strftime("%S", time.localtime()))

        if (curTime - io2.LastTimeDidChecks) > 86400 or (curTime - io2.LastTimeDidChecks) < 3:
            io2.LastTimeDidChecks = curTime

            if settings[0][12] == 1:  # проверяем обновления
                if io2.update()==True:
                    print("Найдено обновление, необходим перезапуск программы!")
                    return

            if settings[0][6] > 0:  # проверяем лишние резервные копии
                io2.backupRestore(delete=True, silent=True)

            if settings[0][11] == 1:
                print("Выясняем встречи на сегодня")
                if len(datedFlats) > 0:
                    dialogs.dialogNotify("Внимание", "Сегодня у вас встреча!")

            print("Определяем начало нового месяца")
            savedMonth = settings[3]
            currentMonth = time.strftime("%b", time.localtime())
            if savedMonth != currentMonth:
                reports.report(newMonthDetected=True)
                settings[3] = time.strftime("%b", time.localtime())
                settings[2][11] = 1

            if settings[2][11] == 1:
                print("Проверяем сдачу отчета")
                answer = dialogs.dialogConfirm(
                    title=icon("lamp") + " Отчет",
                    message=" Вы уже сдали отчет?"
                )
                if answer == True:
                    reports.report(disableNotification=True)
                else:
                    reports.report(showLastMonth=True)

            io2.save(forced=True)

            print("Все готово!")

        if reports.updateTimer(settings[2][6]) >= 0: # проверка, включен ли таймер
            time2 = reports.updateTimer(settings[2][6])
        else:
            time2 = reports.updateTimer(settings[2][6]) + 24
        if settings[2][6] > 0:
            timerTime = " \u2b1b %s" % reports.timeFloatToHHMM(time2)  # check if timer is on to show time
        else:
            timerTime = " \u25b6"

        if settings[2][11]==1:
            remind = icon("lamp")
        else:
            remind=""

        if settings[0][3] != 0:

            if settings[0][2] == True:  # включен кредит часов
                credit = settings[2][1]
            else:
                credit = 0
            gap = float((settings[2][0] + credit) - int(time.strftime("%d", time.localtime())) * settings[0][3] / reports.days())
            if gap >= 0:
                gap_str = icon("extra")
            else:
                gap_str = icon("slippage")
        else:
            gap_str = ""

        housesDue=0 # подсчет просроченных домов
        for h in range(len(houses)):
            if house_op.days_between(
                    houses[h].date,
                    time.strftime("%Y-%m-%d", time.localtime())
            ) > 180:  # сколько просроченных домов
                housesDue += 1
        if housesDue==0:
            due = ""
        else:
            due = icon("lamp")

        options = [
                icon("globe") +   " Участки (%d)" % len(houses),
                icon("contacts")+ " Контакты (%d)  %s" % (totalContacts, appointment),
                icon("report") +  " Отчет (%s) %s %s" % (reports.timeFloatToHHMM(settings[2][0]), gap_str, remind),
                icon("notebook")+ " Блокнот (%d)" % len(resources[0]),
                icon("search")  + " Поиск",
                icon("stats")   + " Статистика %s" % due,
                icon("calendar")+ " Служебный год",
                icon("file")    + " Файл " + io2.getDBCreatedTime(),
                icon("preferences")+" Настройки"
                ]

        if io2.Mode == "sl4a":
            title = "%s Rocket Ministry (v. %s) %s" % ( icon("rocket"), io2.Version, reports.getTimerIcon(settings[2][6]) )
        else:
            title = "%s Rocket Ministry (v. %s)" % (reports.getTimerIcon(settings[2][6]), io2.Version)
            options.append(icon("timer") + " Таймер" + timerTime)  # positive button

        if io2.Mode == "sl4a": # очистка экрана на всякий случай
            from os import system
            try:
                system("clear")
            except:
                system('cls')

        # Run home screen

        choice = dialogs.dialogList(
            form = "home",
            title = title,
            options = options,
            negative = "Выход",
            positiveButton = True,
            negativeButton=False,
            positive = icon("timer") + " Таймер" + timerTime
        )
        if choice == None and io2.Mode=="easygui" and settings[0][1]==0:
            return
        elif choice=="positive": # таймер
            if settings[2][6] == 0:
                reports.report(choice="=(")
            else:
                if settings[0][2]==False:
                    reports.report(choice="=)")  # запись обычного времени
                else: # если в настройках включен кредит, спрашиваем:
                    choice2=dialogs.dialogList(
                        title="Запись времени",
                        options=[
                            icon("timer") + " Обычное время",
                            icon("credit") + " Кредит"
                        ],
                        negative="Отмена"
                    )
                    if choice2==0:
                        reports.report(choice="=)") # запись обычного времени
                    elif choice2==1:
                        reports.report("=$") # запись кредита
            continue
        elif set.ifInt(choice) == True:
            result = options[choice]
        else:
            continue

        if "Участки" in result:
            territory.terView() # territory

        elif "Отчет" in result:
            reports.report() # report

        elif "Контакты" in result:
            contacts.showContacts() # contacts

        elif "Блокнот" in result:
            notebook.showNotebook() # notebook

        elif "Поиск" in result:
            search(query="") # search

        elif "Статистика" in result:
            stats() # stats

        elif "Служебный год" in result:
            serviceYear() # service year

        elif "Файл" in result:
            tools() # tools

        elif "Настройки" in result:
            preferences()
            continue

        elif "Выход" in result:
            return "quit"

def tools():
    """ Program settings on the start screen """

    while 1:

        options = [
            icon("restore") + " Восстановление резервной копии",
            icon("export") + " Экспорт",
            icon("clear") + " Очистка"
        ]

        if io2.Mode == "sl4a":
            options.insert(0, icon("download") + " Импорт из загрузок")
        else:
            options.insert(0, icon("import") + " Импорт из файла")

        if io2.Simplified == False:
            options.insert(1, icon("import") + " Импорт из буфера")
            options.append(icon("load") + " Загрузка")
            options.append(icon("save") + " Сохранение")

        choice = dialogs.dialogList(  # display list of settings
            form="tools",
            title=icon("file") + " Файловые операции " + reports.getTimerIcon(settings[2][6]),
            message="Выберите действие:",
            options=options
        )
        if choice == None:
            break
        else:
            result = options[choice]

        if "Сохранение" in result:
            io2.save(forced=True)  # save

        elif "Загрузка" in result:
            io2.houses.clear()
            io2.settings.clear()
            io2.resources.clear()
            io2.settings[:] = io2.initializeDB()[1][:]
            io2.resources[:] = io2.initializeDB()[2][:]
            io2.load(forced=True)  # load
            io2.save()

        elif "Экспорт" in result:
            io2.share()  # export

        elif "Импорт из загрузок" in result: # для Android
            if dialogs.dialogConfirm(
                    title="Импорт",
                    message="Будет выполнен импорт базы данных из папки загрузок устройства. При сбоях восстановите резервную копию последней работоспособной версии. Продолжать?"
            ) == True:
                io2.load(download=True, delete=True, forced=True)
                io2.save()

        elif "Импорт из буфера" in result: # для Windows
            io2.load(clipboard=True, forced=True)

        elif "Импорт из файла" in result: # для Windows
            if dialogs.dialogConfirm(
                title="Импорт",
                message="Будет выполнен импорт базы данных из внешнего файла. Можно указать его в настройках, тогда он запрашиваться не будет. При сбоях восстановите резервную копию последней работоспособной версии. Продолжать?"
            )==True:
                io2.load(dataFile=settings[0][14], forced=True, delete=True)
                io2.save()
            else:
                continue

        elif "Восстановление" in result:  # restore backup
            io2.backupRestore(restore=True)
            io2.save()

        elif "Очистка" in result:
            if dialogs.dialogConfirm(
                title=icon("clear") + " Очистка",
                message="Все данные программы будут полностью удалены, включая все резервные копии! Вы уверены, что это нужно сделать?"
            )==True:
                io2.clearDB()
                io2.log("База данных очищена!")
                #io2.save()
        else:
            continue

    return False

def toggle(setting):
    if setting == 1:
        return 0
    else:
        return 1

def preferences():
    """ Program preferences """

    def status(setting):
        """ Переключение настройки """
        if setting != 0:
            return icon("mark") + " "
        else:
            return icon("box") + " "
    exit = 0

    while 1:
        options = []
        if settings[0][14] != "":
            importURL = "%s..." % settings[0][14][:15]
        else:
            importURL = "нет"
        if settings[0][17] != "":
            password = settings[0][17]
        else:
            password = "нет"

        options.append(status(settings[0][7])  + "Автоматически записывать повторные посещения")
        options.append(status(settings[0][10]) + "Умная строка в первом посещении")
        options.append(status(settings[0][2])  + "Кредит часов")
        options.append(status(settings[0][11]) + "Уведомления о встречах на сегодня")
        options.append(status(settings[0][8])  + "Напоминать о сдаче отчета")
        options.append(status(settings[0][15]) + "Переносить минуты отчета на следующий месяц")
        options.append(status(settings[0][20]) + "Предлагать разбивку по этажам после добавления квартир")
        if io2.Mode == "sl4a":
            options.append(status(settings[0][0])+"Бесшумный режим при включенном таймере")
        options.append(                       "%s Месячная норма часов: %d" % (icon("circle"), settings[0][3]))
        options.append(status(settings[0][21]) + "Статус обработки подъездов")
        options.append(status(settings[0][9]) + "Последний символ посещения влияет на статус контакта")
        options.append(                       "%s Число резервных копий: %d" % (icon("circle"), settings[0][6]))
        if io2.Mode!="sl4a":
            options.append(                   "%s Файл импорта базы данных: %s" % (icon("circle"), importURL))
        options.append(                       "%s Пароль на вход: %s" % (icon("circle"), password))
        options.append(status(settings[0][16]) + "Режим смайликов")
        options.append(status(settings[0][12]) + "Проверять обновления")
        if io2.Mode != "text":
            options.append(status(settings[0][1])+"Консольный режим")

        # settings[0][4] - занято под сортировку контактов!
        # settings[0][19] - занято под сортировку участков!

        # Свободные настройки:
        # settings[0][13]
        # settings[0][18]

        choice = dialogs.dialogList(  # display list of settings
            form="preferences",
            title=icon("preferences") + " Настройки " + reports.getTimerIcon(settings[2][6]),
            options=options,
            negative="Назад"
        )

        if choice==None:
            break
        elif set.ifInt(choice) == True:
            result = options[choice]
        else:
            continue

        if "Бесшумный режим" in result:
            settings[0][0] = toggle(settings[0][0])
            io2.save()

        elif "Кредит часов" in result:
            settings[0][2] = toggle(settings[0][2])
            io2.save()

        elif "Месячная норма" in result:
            while 1:
                choice2 = dialogs.dialogText(
                    title="Месячная норма",
                    message="Введите месячную норму часов для подсчета запаса или отставания от нормы по состоянию на текущий день. Если эта функция не нужна, введите пустую строку или 0:",
                    default=str(settings[0][3])
                )
                try:
                    if choice2 != None:
                        if choice2 == "":
                            settings[0][3] = 0
                        else:
                            settings[0][3] = int(choice2)
                        io2.save()
                    else:
                        break
                except:
                    io2.log("Не удалось изменить, попробуйте еще")
                    continue
                else:
                    break

        elif "Число резервных копий" in result:  # backup copies
            while 1:
                choice2 = dialogs.dialogText(
                    title="Число резервных копий",
                    message="От 0 до 10 000:",
                    default=str(settings[0][6]),
                )
                try:
                    if choice2 != None:
                        settings[0][6] = int(choice2)
                        if settings[0][6] > 10000:
                            settings[0][6] = 10000
                        elif settings[0][6] < 0:
                            settings[0][6] = 0
                        io2.save()
                    else:
                        break
                except:
                    io2.log("Не удалось изменить, попробуйте еще")
                    continue
                else:
                    break

        elif "Автоматически записывать" in result:
            settings[0][7] = toggle(settings[0][7])
            io2.save()

        elif "Режим смайликов" in result:
            settings[0][16] = toggle(settings[0][16])
            io2.save()

        elif "Статус обработки подъездов" in result:
            settings[0][21] = toggle(settings[0][21])
            if settings[0][21]==1:
                dialogs.dialogHelp(
                    title="Статус обработки подъездов",
                    positiveButton=True,
                    negativeButton=False,
                    message="При включении этого параметра вы сможете указывать для каждого подъезда участка, когда вы в нем были:\n\nв будний день в первой половине дня (первый кружок – 🟡);\n\nв будний день вечером (второй кружок – 🟣);\n\nв выходной (третий кружок – 🔴).\n\nЕсли подъезд посещен все три раза, он показан как обработанный в разделе статистики."
                )
            io2.save()

        elif "Умная строка в первом посещении" in result:
            settings[0][10] = toggle(settings[0][10])
            io2.save()

        elif "Напоминать о сдаче" in result:
            settings[0][8] = toggle(settings[0][8])
            io2.save()

        elif "Предлагать разбивку" in result:
            settings[0][20] = toggle(settings[0][20])
            io2.save()

        elif "Уведомления о встречах" in result:
            settings[0][11] = toggle(settings[0][11])
            io2.save()

        elif "Проверять обновления" in result:
            settings[0][12] = toggle(settings[0][12])
            io2.save()

        elif "Последний символ" in result:
            settings[0][9] = toggle(settings[0][9])
            if settings[0][9]==1:
                dialogs.dialogHelp(
                    title="Последний символ посещения влияет на статус контакта",
                    message="Внимание, вы входите в зону хардкора! :) При включении этого параметра в конце каждого посещения должна стоять цифра от 0 до 4, определяющая статус (в стиле «умной строки», только во всех посещениях):\n\n0 = %s\n1 = %s\n2 = %s\n3 = %s\n4 = %s\n\nЭто должен быть строго последний символ строки. При отсутствии такой цифры статус контакта становится неопределенным (%s)." %
                            ( icon("reject"), icon("interest"), icon("green"), icon("purple"), icon("danger"), icon("question")),
                    positiveButton = True,
                    negativeButton = False,
                ),
            io2.save()

        elif "Файл импорта" in result:
            choice2 = dialogs.dialogFileOpen(default=settings[0][14])
            if choice2 != None:
                settings[0][14] = choice2.strip()
                io2.save()

        elif "Переносить минуты" in result:
            settings[0][15] = toggle(settings[0][15])
            io2.save()

        elif "Консольный режим" in result:
            settings[0][1] = toggle(settings[0][1])
            io2.save()

        elif "Пароль на вход" in result:
            choice2 = dialogs.dialogText(
                title=icon("preferences") + " Пароль на вход",
                message="Введите пароль для входа в программу. Если оставить поле пустым, пароль запрашиваться не будет:",
                default=str(settings[0][17])
            )
            if choice2 != None:
                settings[0][17] = choice2
                io2.save()

    if exit == 1:
        return True

def stats():
    status0 = status1 = status2 = status3 = status4 = nostatus = statusQ = returns = returns1 = returns2 = housesDue = porches = porchesCompleted = 0
    flats = records = 0.0

    # while 1:
    # Counting everything
    for h in range(len(houses)):
        d1 = houses[h].date
        d2 = time.strftime("%Y-%m-%d", time.localtime())
        if house_op.days_between(d1, d2) > 122:  # сколько просроченных домов
            housesDue += 1

        for p in range(len(houses[h].porches)):
            porches += 1
            if io2.Simplified==False:
                if houses[h].porches[p].status == "🟡🟣🔴":  # сколько подъездов обработано
                    porchesCompleted += 1

            for f in range(len(houses[h].porches[p].flats)):
                flats += 1
                if houses[h].porches[p].flats[f].status == "0":  # сколько квартир в разных статусах
                    status0 += 1
                if houses[h].porches[p].flats[f].status == "1":
                    status1 += 1
                if houses[h].porches[p].flats[f].status == "2":
                    status2 += 1
                if houses[h].porches[p].flats[f].status == "3":
                    status3 += 1
                if houses[h].porches[p].flats[f].status == "4":
                    status4 += 1
                if houses[h].porches[p].flats[f].status == "?":
                    statusQ += 1
                if houses[h].porches[p].flats[f].status == "":
                    nostatus += 1
                if len(houses[h].porches[p].flats[f].records) > 1:  # квартир с более чем одной записью
                    returns += 1
                if len(houses[h].porches[p].flats[f].records) == 1:  # квартир с одной записью
                    returns1 += 1
                if len(houses[h].porches[p].flats[f].records) >= 2:  # квартир с более чем двумя записями
                    returns2 += 1

    if housesDue == 0:
        due = ""
    else:
        due = icon("lamp")
    if records == 0:
        records = 0.0001
    if porches == 0:
        porches = 0.0001
    if flats == 0:
        flats = 0.0001  # чтобы не делить на ноль

    message =    "Участков: " + str(len(houses)) +\
                "\nПросрочено: %d %s" % (housesDue, due) +\
                "\n\nВсего квартир: %d" % flats +\
                "\n\nВ статусе %s: %s (%d%%)" % (icon("reject"), str(status0), status0 / flats * 100) +\
                "\nВ статусе %s: %s (%d%%)" % (icon("interest"), str(status1), status1 / flats * 100) + \
                "\nВ статусе %s: %s (%d%%)" % (icon("green"), str(status2), status2 / flats * 100) + \
                "\nВ статусе %s: %s (%d%%)" % (icon("purple"), str(status3), status3 / flats * 100) + \
                "\nВ статусе %s: %s (%d%%)" % (icon("danger"), str(status4), status4 / flats * 100) + \
                 "\n\nБез посещений: %d (%d%%)" % (
                flats - returns1 - returns2, (flats - returns1 - returns2) / flats * 100) +\
                "\nС одним посещением: %d (%d%%)" % (returns1, returns1 / flats * 100) +\
                "\nС повт. посещениями: %d (%d%%)" % (returns2, returns2 / flats * 100)

    if settings[0][21]==1:
        message += "\n\nОбработано подъездов: %d/%d (%d%%)" % \
                        (porchesCompleted, porches, porchesCompleted / porches * 100)

    dialogs.dialogHelp(title=icon("stats") + " Статистика " + reports.getTimerIcon(settings[2][6]), message=message)


def search(query=""):
    """ Search flats/contacts """

    if query == "":
        exit = 0
    else:
        exit = 1  # если поисковый запрос задан, только показать результат и выйти
    while 1:
        if query == "":
            query = dialogs.dialogText(  # get search query
                title = icon("search") + " Поиск " + reports.getTimerIcon(settings[2][6]),
                default="",
                message="Найдите любую квартиру или контакт:",
                neutralButton=True,
                neutral="Очист."
            )
            if io2.Mode == "sl4a" and settings[0][1] == False:
                from androidhelper import Android
                phone = Android()
                phone.dialogCreateSpinnerProgress(title="Prompt Ministry", message="Ищем", maximum_progress=100)

        elif query == None:
            return

        elif query != None:

            # Valid query, run search

            while 1:
                query = query.lower()
                query = query.strip()
                allContacts = contacts.getContacts(forSearch=True)
                list = []

                for i in range(len(allContacts)):  # start search in flats/contacts
                    found = False
                    if query in allContacts[i][2].lower() or query in allContacts[i][2].lower() or query in \
                            allContacts[i][3].lower() or query in allContacts[i][8].lower() or query in allContacts[i][
                        10].lower() or query in allContacts[i][11].lower() or query in allContacts[i][
                        12].lower() or query in allContacts[i][13].lower():
                        found = True

                    if allContacts[i][8] != "virtual":
                        for r in range(len(houses[allContacts[i][7][0]].porches[allContacts[i][7][1]].flats[
                                               allContacts[i][7][2]].records)):  # in records in flats
                            if query in houses[allContacts[i][7][0]].porches[allContacts[i][7][1]].flats[
                                allContacts[i][7][2]].records[r].title.lower():
                                found = True
                            if query in houses[allContacts[i][7][0]].porches[allContacts[i][7][1]].flats[
                                allContacts[i][7][2]].records[r].date.lower():
                                found = True
                    else:
                        for r in range(len(resources[1][allContacts[i][7][0]].porches[0].flats[
                                               0].records)):  # in records in contacts
                            if query in resources[1][allContacts[i][7][0]].porches[0].flats[0].records[r].title.lower():
                                found = True
                            if query in resources[1][allContacts[i][7][0]].porches[0].flats[0].records[r].date.lower():
                                found = True

                    if found == True:
                        list.append([allContacts[i][7], allContacts[i][8], allContacts[i][2]])

                options2 = []
                for i in range(len(list)):  # save results
                    if list[i][1] != "virtual":  # for regular flats
                        options2.append("%d) %s-%s" % (i + 1, houses[list[i][0][0]].title,
                                                       houses[list[i][0][0]].porches[list[i][0][1]].flats[
                                                           list[i][0][2]].title))
                    else:  # for standalone contacts
                        options2.append("%d) %s, %s" % (
                            i + 1, resources[1][list[i][0][0]].title,
                            resources[1][list[i][0][0]].porches[0].flats[0].title)
                                        )

                if len(options2) == 0:
                    options2.append("Ничего не найдено")

                if io2.Mode == "sl4a" and settings[0][1] == False:
                    phone.dialogDismiss()

                choice2 = dialogs.dialogList(
                    form="search",
                    title=icon("search") + " Поиск по запросу «%s»" % query,
                    message="Результаты:",
                    options=options2
                )

                # Show results

                if choice2 == None:
                    if exit == 1:
                        return
                    else:
                        query = ""
                        break

                elif choice2 == "":
                    if exit == 1:
                        return
                    if settings[0][1] == True:
                        break

                elif not "не найдено" in options2[0]:  # go to flat
                    h = list[choice2][0][0]  # получаем номера дома, подъезда и квартиры
                    p = list[choice2][0][1]
                    f = list[choice2][0][2]
                    if list[choice2][1] != "virtual":  # regular contacts
                        territory.flatView(flat=houses[h].porches[p].flats[f], house=houses[h])
                    else:  # standalone contacts
                        territory.flatView(flat=resources[1][h].porches[0].flats[0], house=resources[1][h], virtual=True)

def serviceYear():
    while 1:
        options = []
        for i in range(12):  # filling options by months
            if i < 4:
                monthNum = i + 9
            else:
                monthNum = i - 3
            if settings[4][i] == None:
                options.append(reports.monthName(monthNum=monthNum)[0])
            else:
                if settings[4][i] == settings[0][3]:
                    check = icon("mark")
                elif settings[4][i] < settings[0][3]:
                    check = icon("fail")
                elif settings[4][i] > settings[0][3] and settings[0][3] != 0:
                    check = icon("up")
                else:
                    check = ""
                options.append("%s %d %s" % ((reports.monthName(monthNum=monthNum)[0] + ":", settings[4][i], check)))

        if io2.Mode != "sl4a":
            options.append(icon("calc") + " Аналитика")  # neutral button on Android

        #if int(time.strftime("%m", time.localtime())) <= 9:  # current service year, changes in October
        #    year = "%d" % int(time.strftime("%Y", time.localtime()))
        #else:
        #    year = "%d" % int(time.strftime("%Y", time.localtime()))

        hourSum = 0.0  # total sum of hours
        monthNumber = 0  # months entered
        for i in range(len(settings[4])):
            if settings[4][i] != None:
                hourSum += settings[4][i]
                monthNumber += 1
        yearNorm = float(settings[0][3]) * 12  # other stats
        gap = (12 - monthNumber) * float(settings[0][3]) - (yearNorm - hourSum)
        if gap >= 0:
            gapEmo = icon("extra")
            gapWord = "Запас"
        elif gap < 0:
            gapEmo = icon("slippage")
            gapWord = "Отставание"
        else:
            gapEmo = ""

        # Display dialog

        choice = dialogs.dialogList(
            title="%s Всего %s ч. ⇨ %+d %s %s" % (
                icon("calendar"),
                reports.timeFloatToHHMM(hourSum)[ 0 : reports.timeFloatToHHMM(hourSum).index(":") ],
                gap,
                gapEmo,
                reports.getTimerIcon(settings[2][6])
            ),
            message="Выберите месяц:",
            form="serviceYear",
            neutralButton=True,
            neutral=icon("calc") + " Аналитика",
            options=options)

        if choice == None:
            break

        elif choice == "neutral":  # calc

            if monthNumber != 12:
                average = (yearNorm - hourSum) / (12 - monthNumber)  # average
            else:
                average = yearNorm - hourSum
            dialogs.dialogHelp(
                title="%s Аналитика" % icon("calc"),
                message="Месяцев введено: %d\n\n" % monthNumber +
                        "Часов введено: %d\n\n" % hourSum +
                        "Годовая норма¹: %d\n\n" % yearNorm +
                        "Осталось часов: %d\n\n" % (yearNorm - hourSum) +
                        "%s: %d %s\n\n" % (gapWord, abs(gap), gapEmo) +
                        "Среднее за месяц²: %0.f\n\n" % average +
                        "____\n" +
                        "¹ Равна 12 * месячная норма (в настройках).\n\n" +
                        "² Среднее число часов, которые нужно служить каждый месяц в оставшиеся (не введенные) месяцы.\n\n"
            )
        else:
            if choice < 4:
                monthNum = choice + 9
            else:
                monthNum = choice - 3

            if settings[4][choice]!=None:
                options2 = [icon("edit") + " Править ", icon("cut") + " Очистить "]
                choice2 = dialogs.dialogList(
                    title=icon("report") + " %s" % reports.monthName(monthNum=monthNum)[0],
                    options=options2,
                    message="Что делать с месяцем?",
                    form="noteEdit"
                )
            else:
                choice2=0

            if choice2 == 0:  # edit
                if settings[4][choice] != None:
                    default = str(int(settings[4][choice]))
                else:
                    default = ""
                message="Введите значение этого месяца:"
                while 1:
                    choice3 = dialogs.dialogText(
                        title=icon("report") + " %s" % reports.monthName(monthNum=monthNum)[0],
                        message=message,
                        default=default
                    )
                    if choice3 == None:
                        break
                    elif "cancelled!" in choice3:
                        continue
                    elif set.ifInt(choice3)==False or int(choice3)<0:
                        message="Требуется целое положительное число:"
                    else:
                        settings[4][choice] = int(choice3)
                        io2.save()
                        break

            if choice2 == 1:
                settings[4][choice] = None  # clear
                io2.save()
            else:
                continue
