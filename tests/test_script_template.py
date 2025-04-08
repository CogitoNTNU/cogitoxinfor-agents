from persistent_browser import start_browser
import time

def run_test():
    # Hent den allerede åpne vedvarende konteksten (login er allerede gjort)
    context = start_browser()
    
    # Bruk den første eksisterende fanen, eller opprett en ny hvis ingen faner finnes
    pages = context.pages
    if len(pages) == 0:
        page = context.new_page()
    else:
        page = pages[0]



    # Begge linker MÅ være med i hver test, ellers vil ikke testene fungere. Først navigeres det til login-URLen for autologin
    page.goto("https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b")
    time.sleep(12)
    page.goto("https://m3prduse1b.m3.inforcloudsuite.com/mne/ext/h5xi/?LogicalId=lid:%2F%2Finfor.m3.m3&inforCurrentLanguage=en-US&LNC=GB&inforCurrentLocale=en-US&inforTimeZone=(UTC%2B00:00)%20Dublin,%20Edinburgh,%20Lisbon,%20London&xfo=https:%2F%2Fmingle-portal.inforcloudsuite.com&inforThemeName=Light&inforThemeColor=amber&inforOSPortalVersion=2025.03.03")

    # Her kan du legge til din testkode (for eksempel sjekke elementer eller utføre handlinger)
    input("Testen er ferdig. Trykk Enter for å lukke testfanen...")
    page.close()

if __name__ == '__main__':
    run_test()