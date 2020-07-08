# Mini Project 1
# Nectarios Chroniaris & Maaz Siddique

import sqlite3, sys, os
from getpass import getpass
from re import fullmatch
from math import ceil

# We define the connection and cursor as global variables so they can be accessed by all functions.
conn = None
c = None

# Main function and control loop
def main(argc, argv):

    # Checks the amount of arguments is exactly one for specifying the database.
    if argc != 1:
        print('Usage: mp1.py database_name.db')
        return -1

    # Checks if the database being specified exists. It wouldn't make much sense to open a database meant for authentication with no schema or data.
    if not os.path.exists(argv[0]):
        print('The database \'{}\' does not exist. Please check the path argument.'.format(argv[0]))
        return -1

    # Connect to the database
    connect(argv[0])

    # This is the core loop for handling multiple user sessions. It calls login once every loop and checks the return value. A valid login is represented by a email string, and an invalid login attempt is a return value of NoneType. If it is None, then we know that the user has called the exit function, so we appropriately terminate.
    while True:
        email = login()

        # If the user types 'exit' in loginPage(), it propagates up here and we quit the program
        if (email == None):
            print('\nQuitting...')
            break

        mainMenu(email)

    # Closes the connection
    conn.close()

    return

##
#### Login, Registration, and core menu functions start here ####
##

# Connects to a specified database specified with path. It creates a connection, a cursor, and turns foreign key constraints on.
def connect(path):

    # We declare globals conn and c since we must modify them directly. This statement should not appear in any other function since we should never re-modify where conn or c points to.
    global conn, c

    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys = ON;')
    conn.commit()

    return

# This function semantically "logs in" a user, based on the email that is returned from loginPage(). After a valid email has been passed, it prints unread messages for that user, sets them to read, and then prompts the user to enter the main menu. i.e. it returns to main() with the valid "logged in" email.
def login():
    # We attempt to sign in a user using loginPage(). Assuming that a valid email has been returned, it is already in lowercase.
    email = loginPage()

    # We must check this since past this point we assume that a user (denoted by email) is registered. If email == None, then that means we have failed to authenticate a user and have received an exit command.
    if email == None:
        return

    # At this point we consider the user logged in.
    os.system('clear||cls')

    # Prints a welcome message to the user.
    c.execute('SELECT name FROM members WHERE lower(email) = ?;', (email,))
    print('Logged in as user \'{}\' ({}).\n'.format(c.fetchone()[0], email))

    # Query for getting all the info for each message
    qGetMessages = '''

        SELECT
            sender,
            DATE(msgTimestamp),
            TIME(msgTimestamp),
            content
        FROM
            inbox
        WHERE
            lower(email) = ?
            AND lower(seen) = 'n' ;

    '''

    # Fetches all unread messages and stores them in messageList
    c.execute(qGetMessages, (email,))
    messageList = c.fetchall()

    # Prints all unread messages
    for message in messageList:
        print('Message from \'{}\' on {}, {}:\n\t\"{}\"\n'.format(*message))

    # Print a message if there are no unread messages
    if (not messageList):
        print('No new messages.\n')

    # Set all unread messages to read
    c.execute('UPDATE inbox SET seen = \'y\' WHERE email = ?', (email,))
    conn.commit()

    # Prompt user to advance to the main menu
    input('Press the enter key to advance to the main menu. ')

    return email

# This function handles the input of usernames and passwords passed into the program by the user. It calls authenticateUser() with an email and password. If this returns true, we return to the login() with the email string so that it can actually "log [the user] in". If the input passed by the user is 'register' then we call registerUser(). Whether that suceeds or fails we restart the login page. If the input passed by the user is 'exit', then we immediately return None. We have two nested loops so we can clear the terminal after a registration. The inner loop will always loop when an email/password combo fails but the only time the outer loop will restart is when registerUser() is called and returned (which is why the break statement is there).
def loginPage():
    while True:

        # Clears the console.
        os.system('clear||cls')

        print('This is the login page. Please type a valid email or type \'register\' to register as a new user. Type \'exit\' to exit the login screen.\n')

        # We keep this in a loop to give the user multiple attempts to log in to any account, or to register and login as may times as they'd like.
        while True:

            # Getting plaintext email from the user. We convert it to lowercase to get past any casing issues.
            email = (input('Email: ')).lower().strip()

            # If input is 'exit', we return. If the input is 'register', then we call registerUser() and once that function is done (regardless if any changes were made) we continue the loop to attempt to log the user in again.
            if (email == 'exit'):
                return
            elif (email == 'register'):
                registerUser()
                break

            # Getting non-echoed password from user using the getpass() function of the getpass library.
            password = getpass('Password: ')

            if (authenticateUser(email, password)):
                return email
            else:
                print('\nAuthentication failed. Please check your credentials.')

            # For formatting purposes
            print()

    return

# Checks if the email & password combo exists in the database.
def authenticateUser(email, password):

    # Defines the query for autenticating users
    pQuery = '''

        SELECT
            COUNT(email)
        FROM
            members
        WHERE
            lower(email) = ?
            AND pwd = ? ;

    '''

    # Executes the query above with the passed email and password
    c.execute(pQuery, (email, password))

    # If the count from the query is exactly 1, that means that one user exactly was authenticated with a matching email and password. Since the expression would resolve to a boolean value, the return value is either True or False.
    return (c.fetchone()[0] == 1)

# The main idea of this function is that for any required information it runs a check loop. It grabs a value from the user and runs a series of checks on them. If they fail, we restart the check loop. If they all pass, we break the loop at the end. It then goes onto the next loop. At any point we recieve 'exit' we return to the loginPage().
def registerUser():

    # Clears console
    os.system('clear||cls')

    print('This is the registration page. Please type a valid email address and then a password. Type \'exit\' at any point to exit the registration page.\n')

    # Email match loop
    while True:
        # Gets email from the user. Strips leading and trailing whitespace characters.
        email = input('Email (registration): ').lower().strip()

        if (email == 'exit'):
            return

        # Uses Regex to match a valid email address. Complains if it does not match.
        if (fullmatch('^\\b[a-z0-9._-]+@[a-z0-9.-]+\\.[a-z]{1,}\\b$', email) == None):
            print('This is not a valid formatted email address. Please try again.')
            continue

        # Makes sure that the email address is not already in the database. We call lower() to
        c.execute('SELECT COUNT(email) FROM members WHERE lower(email) = ?;', (email,))
        if (c.fetchone()[0] != 0):
            print('The email you specified already exists. Please enter another email address.')
            continue

        break

    # Password match loop
    while True:

        # Gets password
        password = getpass('Password (registration): ')

        if (password == 'exit'):
            return

        # Gets a retyped password to verify.
        if (getpass('Retype password: ') != password):
            print('Passwords are mismatched. Please recreate your password.')
            continue

        break

    # Name match loop
    while True:

        # Gets name. Strips leading and trailing whitespace characters.
        name = input('Name (registration): ').strip()

        if (name == 'exit'):
            return

        if (len(name) < 1):
            print('Name cannot be empty. Please enter a valid name.')
            continue

        break

    # Phone match loop
    while True:

        # Gets phone number
        phone = input('Phone number (registration): ').strip()

        if (phone == 'exit'):
            return

        if (fullmatch('^[0-9]\d{2}-\d{3}-\d{4}$', phone) == None):
            print('This phone number is not valid. Please enter a valid phone number of form XXX-XXX-XXXX.')
            continue

        break

    # Register the user. At this point all values should have passed their respective checks so we can assume everything is valid.
    c.execute('INSERT INTO members VALUES (?, ?, ?, ?)', (email, name, phone, password))
    conn.commit()

    # Print success message
    print('\nSuccessfully registered member with email address \'{}\'.'.format(email))

    # Prompt user to return back
    input('Press the enter key to return to the login page. ')

    return

# This function handles the main menu functions, and calls all core functionality (book rides, etc.), all assuming a user is authenticated. As a result it calls loginPage() first to try to authenticate/register a user.
def mainMenu(email):

    while True:

        os.system('clear||cls')

        # Prints welcome message again
        c.execute('SELECT name FROM members WHERE lower(email) = ?;', (email,))
        print('Logged in as user \'{}\' ({}).\n'.format(c.fetchone()[0], email))

        print('This is the main menu. Type \'help\' for commands, or \'logout\' to log out.')

        while True:

            command = input('Main Menu > ').lower().strip()

            if (command == 'help'):
                print('    - Command - \t- Description -\n'
                      '    help        \tShow this menu\n'
                      '    logout      \tLogs out of the currently logged-in user\n\n'
                      '    offer       \tOffer a ride (Q1)\n'
                      '    rides       \tSearch for a ride (Q2)\n'
                      '    bookings    \tBook members or cancel bookings (Q3)\n'
                      '    post        \tPost a request (Q4)\n'
                      '    requests    \tSearch or delete ride requests (Q5)\n' )

            elif (command == 'logout'):
                return

            elif (command == 'offer'):
                offerRide(email)
                break

            elif (command == 'rides'):
                searchRide(email)
                break

            elif (command == 'bookings'):
                bookingsPage(email)
                break

            elif (command == 'post'):
                postRideRequest(email)
                break

            elif (command == 'requests'):
                requestsPage(email)
                break

            else:
                print('Unrecognized command. Type \'help\' for help.\n')

    return

##
#### Functions for offering rides start here (Q1) ####
##

# This crazy long function esentially runs a bunch of checks whatever information we need for a ride. It then adds those changes to the database and commits.
def offerRide(email):

    os.system('clear||cls')
    print('You are now attempting to offer a ride. A valid date, number of seats offered, a price per seat, a luggage description, source location, and destination location is required. You have the option of adding a set of enroute locations or a car number. Type \'exit\' at any time to return to the main menu.\n')

    while True:

        # Date checking
        while True:
            date = input('Please type in a date in format YYYY-MM-DD... > ').lower().strip()

            if (date == 'exit'):
                return

            c.execute('SELECT DATE(?);', (date,))

            # Since a format like the following in SQLite is valid (DATE(ddddd...) where d is an integer) we check the number of dashes is exactly equal to 2 so we can avoid this.
            if (not c.fetchone()[0] or date.count('-') != 2):
                print('The date is not valid. Please try again.\n')
                continue

            break

        # Seats checking
        while True:
            seats = input('Please specify the number of seats you want to offer... > ').lower().strip()

            if (seats == 'exit'):
                return

            if (len(seats) < 1):
                print('Seat number cannot be empty. Please try again.\n')
                continue

            try:
                seats = int(seats)
            except ValueError:
                print('The number of seats is not an integer. Please try again.\n')
                continue

            break

        # Price checking
        while True:
            price = input('Please enter the price per seat as an integer... > ').lower().strip()

            if (price == 'exit'):
                return

            if (len(price) < 1):
                print('Price cannot be empty. Please try again.\n')
                continue

            try:
                price = int(price)
            except ValueError:
                print('The price specified is not an integer. Please try again.\n')
                continue

            break

        # Description checking
        while True:
            luggageDesc = input('Please enter luggage description... > ').lower().strip()

            if (luggageDesc == 'exit'):
                return

            if (len(luggageDesc) == 0):
                print('Description cannot be empty. Please try again.\n')
                continue

            break

        # Location checking (source)
        while True:
            srcLocationKeyword = input('Please specify a source location code or a substring...> ').lower().strip()

            if (srcLocationKeyword == 'exit'):
                return

            # Finding locations that match the keyword (substring included)
            results = searchLocation(srcLocationKeyword)

            if (not results):
                print('No locations found for \'{}\'. Please try again.\n'.format(srcLocationKeyword))
                continue

            print('\nDisplaying Results. At any point, you can type \'select\' to select a location code for the ride.')

            formatString = '    {:<15}  {:<11}  {:<15}  {:<15}'
            print(formatString.format(*'Location Code, City, Province, Address'.split(', ')))

            # We define these as lists so they can be mutable down the chain
            srcLocation = []

            # We are running resultsWizard() and checking for the special case, which in our case happens to be failing to select a location.
            if (resultsWizard(email, results, formatString, searchLocationHelper, hfParam = srcLocation) == False):
                print('You have not selected a source location. Please search and try again.\n')
                continue

            break

        # Location checking (destination)
        while True:
            dstLocationKeyword = input('Please specify a destination location code or a substring...> ').lower().strip()

            if (dstLocationKeyword == 'exit'):
                return

            # Finding locations that match the keyword (substring included)
            results = searchLocation(dstLocationKeyword)

            if (not results):
                print('No locations found for \'{}\'. Please try again.\n'.format(dstLocationKeyword))
                continue

            print('\nDisplaying Results. At any point, you can type \'select\' to select a location code for the ride.')

            formatString = '    {:<15}  {:<11}  {:<15}  {:<15}'
            print(formatString.format(*'Location Code, City, Province, Address'.split(', ')))

            # We define these as lists so they can be mutable down the chain
            dstLocation = []

            # We are running resultsWizard() and checking for the special case, which in our case happens to be failting to select a location.
            if (resultsWizard(email, results, formatString, searchLocationHelper, hfParam = dstLocation) == False):
                print('You have not selected a destination location. Please search and try again.\n')
                continue

            break

        # Location checking (enroute)
        while True:
            command = input('Would you like to specify enroute locations? (y/n) > ').lower().strip()

            # We define these as lists so they can be mutable down the chain
            ERLocations = []

            if (command == 'y'):

                while True:

                    ERLocationKeyword = input('Please specify a enroute location code or a substring...> ').lower().strip()

                    if (ERLocationKeyword == 'exit'):
                        return

                    # Finding locations that match the keyword (substring included)
                    results = searchLocation(ERLocationKeyword)

                    if (not results):
                        print('No locations found for \'{}\'. Please try again.\n'.format(ERLocationKeyword))
                        continue

                    print('\nDisplaying Results. At any point, you can type \'select\' to select a location code for the ride.')

                    formatString = '    {:<15}  {:<11}  {:<15}  {:<15}'
                    print(formatString.format(*'Location Code, City, Province, Address'.split(', ')))

                    # We are running resultsWizard() and checking for the special case, which in our case happens to be failting to select a location.
                    if (resultsWizard(email, results, formatString, searchLocationHelper, hfParam = ERLocations) == False):
                        print('You have not selected an enroute location. Please search and try again.\n')
                        continue

                    cont = input('Would you like to continue adding locations? (y for yes, anything else for no) > ').lower().strip()

                    if (cont == 'y'):
                        continue

                    break


            elif (command == 'n'):
                print('Enroute locations will not be added.\n')
            else:
                print('Unrecognized command. Please try again.\n')
                continue

            break

        # Car number checking
        while True:
            command = input('Would you like to specify a car number? (y/n) > ').lower().strip()

            if (command == 'y'):

                while True:

                    cno = input('Please specify a car number...> ').lower().strip()

                    if (cno == 'exit'):
                        return

                    # Finding locations that match the keyword (substring included)
                    c.execute('SELECT owner FROM cars WHERE cno = ?;', (cno,))
                    owner = c.fetchone()

                    if (not owner):
                        print('Car number \'{}\' does not exist. Please try again.\n'.format(cno))
                        continue

                    if (owner[0] != email):
                        print('The car number specified exists, but does not belong to you. You must specify a car that you own.\n')
                        continue

                    break

            elif (command == 'n'):
                print('A car number will not be added.\n')
                cno = None
            else:
                print('Unrecognized command. Please try again.\n')
                continue

            break

        # Compute next rno. If the table has no rides, it starts from one.
        c.execute('SELECT IFNULL(MAX(rno) + 1, 1) FROM rides')
        rno = c.fetchone()[0]

        # Finally add the ride specified
        c.execute('INSERT INTO rides VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (rno, price, date, seats, luggageDesc, srcLocation[0], dstLocation[0], email, cno))

        # Add all enroute locations
        for location in ERLocations:
            c.execute('INSERT INTO enroute VALUES (?, ?)', (rno, location))

        # Commit changes
        conn.commit()

        print('Ride added sucessfully.\n')

        break

    return

# Searches for a exactly matching lcode or a substring of a city, province, or address.
def searchLocation(keyword):

    qSearch = '''

        SELECT
            lcode,
            city,
            prov,
            address
        FROM
            locations
        WHERE
            lower(lcode) = :keyword
            OR city LIKE '%' || :keyword || '%'
            OR prov LIKE '%' || :keyword || '%'
            OR address LIKE '%' || :keyword || '%' ;

    '''

    c.execute(qSearch, {'keyword':keyword})

    return c.fetchall()

# Helper Function that handles the commands for displaying results. Meant to be passed into resultsWizard(). This helper function uses the "special case", hence the non underscore parameter.
def searchLocationHelper(email, location):

    while True:

        command = input('Type \'more\' to see more results or type a command... > ').lower().strip()

        if (command == 'select'):
            validLoc = selectLocation(location)

            if (validLoc):
                print('Valid location code selected. Type exit to return back to the offer page.\n')

            continue
        elif (command == 'more'):
            return True
        elif (command == 'exit'):
            if (not location):
                return False

            return
        else:
            print('Unrecognized command. Valid commands are \'select\', \'more\', and \'exit\'.')

# Small loop to prompt the user to select a location. takes in a location *list* as its parameter since we have to modify it and reference it outside the function.
def selectLocation(location):

    while True:

        locKeyword = input('Type the lcode of the destination you wish to pick... > ').lower().strip()

        c.execute('SELECT COUNT(lcode) FROM locations WHERE lower(lcode) = ?', (locKeyword,))

        if (locKeyword == 'exit'):
            return

        if (c.fetchone()[0] != 1):
            print('The lcode you have specified does not exist. Please try again.\n')
            continue

        location.append(locKeyword)

        return True

##
#### Functions for searching rides start here (Q2) ####
##

# Main control loop for searching lcodes in source ,destination, and enroute locations
def searchRide(email):

    qSearchRides = '''

        SELECT
            r.rno,
            r.price,
            r.rdate,
            r.seats,
            r.lugDesc,
            r.driver,
            c.cno,
            c.make,
            c.model,
            c.year,
            c.seats
        FROM
            rides AS r
        INNER JOIN
            locations AS lSrc ON lSrc.lcode = r.src
        INNER JOIN
            locations AS lDst ON lDst.lcode = r.dst
        LEFT OUTER JOIN
            cars AS c USING(cno)
        LEFT OUTER JOIN
            enroute AS er USING(rno)
        LEFT OUTER JOIN
            locations AS lEr ON lEr.lcode = er.lcode
        WHERE
            lower(lSrc.lcode) = :keyword
            OR lower(lDst.lcode) = :keyword
            OR lower(lEr.lcode) = :keyword

            OR lSrc.city LIKE '%' || :keyword || '%'
            OR lDst.city LIKE '%' || :keyword || '%'
            OR lEr.city LIKE '%' || :keyword || '%'
            OR lSrc.prov LIKE '%' || :keyword || '%'
            OR lDst.prov LIKE '%' || :keyword || '%'
            OR lEr.prov LIKE '%' || :keyword || '%'
            OR lSrc.address LIKE '%' || :keyword || '%'
            OR lDst.address LIKE '%' || :keyword || '%'
            OR lEr.address LIKE '%' || :keyword || '%' ;

    '''

    os.system('clear||cls')
    print('You are now searching for rides matching locations. Type \'exit\' to return to the main menu.\n')

    while True:

        # Get a keyword list from the user. We replace all commas by spaces, and split the resulting string into a list of keywords.
        keywordList = input('Enter 1 to 3 keywords separated by spaces or commas: ').replace(',', ' ').split()

        # Check that the range of keywordList is in [1, 3].
        if len(keywordList) > 0 and len(keywordList) <= 3:

            # Check if the user wants to exit. No IndexError will occur since we are in the if loop that checks the range
            if (keywordList[0] == 'exit'):
                return

            # Define a master result set. We use a set since we want to eliminate duplicates. We'll convert it to a list later to be able to use subscripting.
            results = set()

            # Searches the database once for every keyword. Converts the result list to a set and unions it with results
            for keyword in keywordList:

                c.execute(qSearchRides, {'keyword':keyword})
                results = results.union(set(c.fetchall()))

            # If the length of the result set is 0, then we know that no results have been found
            if len(results) == 0:
                print('No results were found.')
                continue

            # Converts the set to a list so we can use array subscripting.
            results = list(results)

            # Starts displaying results
            print('\nDisplaying Results. At any point, you can type \'send\' to send a message to a specific ride, or press  \'more\' to display more results. Type \'exit\' to return to the search.')

            formatString = '    {:<5}  {:<5}  {:<12}  {:<7}  {:<15}  {:<15}  {:<7}  {:<15}  {:<15}  {:<6}  {:<3}'

            print(formatString.format(*'rno, price, date, seats, Luggage Desc, driver, carno, make, model, year, seats'.split(', ')))

            # Calls the results wizard to display 5 at a time, etc.
            resultsWizard(email, results, formatString, searchRideHelper)

        else:
            print('The number of keywords does not fall between 1 and 3. Please try again.')

        print()

    return

# Small function for handling input for the search "engine" above. Returns True if the user requests more results, and None if the user wants to exit. For sending a message, we call sendMessageHelper(). We have to define an extra parameter because of the way I designed the function.
def searchRideHelper(email, _):

    while True:

        command = input('Type \'more\' to see more results or type a command... > ').lower().strip()

        if (command == 'send'):
            sendMessageHelper(email)
            continue
        elif (command == 'more'):
            return True
        elif (command == 'exit'):
            return
        else:
            print('Unrecognized command. Valid commands are \'more\', \'send\', and \'exit\'.')

    return

# This function handles all input and message sending given a member's email. It prompts the user for a rno and checks if it exists. If it does, it allows them to send a message.
def sendMessageHelper(email):

    print()

    while True:

        rno = input('Please type the ride number (rno) of the ride you want to send a message to or type \'exit\' to return to search... > ').lower().strip()

        if (rno == 'exit'):
            return

        try:
            rno = int(rno)
        except ValueError:
            print('Input is not an integer. Please try again.\n')
            continue

        # Check existence of ride and print appropriate message if it does not.
        c.execute('SELECT driver FROM rides WHERE rno = ? ;', (rno,))

        # In form of 'driver' <-- (driver,)[0]
        driver = c.fetchone()[0]

        # This checks if the rno of that ride exists and grabs the driver.
        if (not driver):
            print('The ride you specified does not exist. Please try again.\n')
            continue

        message = input('Type the message you want to send to \'{}\'... > '.format(driver))

        if (message == 'exit'):
            return

        c.execute('INSERT INTO inbox VALUES (?, DATETIME(\'now\'), ?, ?, ?, \'n\')', (driver, email, message, rno))
        conn.commit()

        print('Message sent.\n')

        return

##
#### Functions for handling bookings of rides start here (Q3) ####
##

# This function is the main control loop for the bookings page. It allows a user to display bookings, add, or cancel them.
def bookingsPage(email):

    os.system('clear||cls')
    print('This is bookings page. Type \'display\' to display your bookings, \'book\' to book a ride, or \'cancel\' to cancel a booking. Type \'exit\' at any point to exit the posting page.\n')

    while True:

        command = input('Enter a command... > ').lower().strip()

        if (command == 'exit'):
            return
        elif (command == 'display'):
            displayBookings(email)
            continue
        elif (command == 'book'):
            displayRides(email)
            continue
        elif (command == 'cancel'):
            cancelBooking(email)
            continue
        else:
            print('Unrecognized command. Valid commands are \'display\', \'book\', \'cancel\', and \'exit\'.\n')
            continue

    return

# This fucntion gets all the available seats from every ride of the user
def displayRides(email):

    qGetRides = '''

        SELECT DISTINCT
            r.rno AS rno,
            IFNULL(SUM(b.seats), 0) AS booked,
            r.seats - IFNULL(SUM(b.seats), 0) AS available,
            r.rdate
        FROM
            rides AS r
        LEFT OUTER JOIN
            bookings AS b ON b.rno = r.rno
        WHERE
            r.driver = ?
        GROUP BY
            r.rno,
            r.seats,
            r.rdate

    '''

    # Gets all the available seats from every ride of the user.
    c.execute(qGetRides, (email,))

    results = c.fetchall()

    print('\nDisplaying Results. At any point, you can type \'book\' to start booking a member to a ride, or press \'more\' to display more results. Type \'exit\' to return to the bookings page.')

    formatString = '    {:<11}  {:<9}  {:<11}  {:<12}'

    print(formatString.format(*'Ride No., Booked, Avaliable, Date'.split(', ')))

    # Calls the results wizard to display 5 at a time, etc.
    resultsWizard(email, results, formatString, addBookingHelper)


    return

# Helper function that is the main control loop for displaying/adding bookings. Meant to be passed into resultsWizard().
def addBookingHelper(email, _):

    while True:

        command = input('Type \'more\' to see more results or type a command... > ').lower().strip()

        if (command == 'book'):
            addBooking(email)
            continue
        elif (command == 'more'):
            return True
        elif (command == 'exit'):
            return
        else:
            print('Unrecognized command. Valid commands are \'more\', \'book\', and \'exit\'.')

    return

# Displays a member's bookings, if any.
def displayBookings(email):

    qGetAllBookings = '''

        SELECT
            b.*
        FROM
            bookings AS b
        INNER JOIN
            rides AS r ON r.rno = b.rno
        WHERE
            lower(r.driver) = ?

    '''

    # Get all of the member's requests
    c.execute(qGetAllBookings, (email,))

    results = c.fetchall()

    # Check if the user has requests
    if (len(results) == 0):
        print('You have no bookings.\n')
        return

    print('Bookings for \'{}\':'.format(email))

    formatString = '    {:<13}  {:<15}  {:<13}  {:<9}  {:<9}  {:<10}  {:<10}'

    # Print table headers
    print(formatString.format(*'Booking No., Email, Ride No., Cost, Seats, Pickup, Dropoff'.split(', ')))

    # Because .format() doesn't like NoneTypes in a format specifier ({:<10} for example), we have to protect againt printing NULLs
    for r in results:
        print(formatString.format(r[0], r[1], r[2], r[3] or 'NULL', r[4] or 'NULL', r[5] or 'NULL', r[6] or 'NULL'))

    return

# This function allows a user to add a booking based on certain values that are checked.
def addBooking(email):

    qGetSeats = '''

        SELECT DISTINCT
            r.seats - IFNULL(SUM(b.seats), 0) AS available
        FROM
            rides AS r
        LEFT OUTER JOIN
            bookings AS b ON b.rno = r.rno
        WHERE
            r.rno = ?
        GROUP BY
            r.rno,
            r.seats

    '''

    # Ride Number Checking
    while True:
        rno = input('Enter an ride number (rno) (creating booking)... > ').lower().strip()

        if (rno == 'exit'):
            return

        # Verifies if rno exists
        c.execute('SELECT COUNT(rno) FROM rides WHERE rno = ? ;', (rno,))

        if (c.fetchone()[0] != 1):
            print('The ride number \'{}\' does not exist. Please try again.\n'.format(rno))
            continue

        c.execute('SELECT COUNT(rno) FROM rides WHERE rno = ? AND driver = ? ;', (rno, email))

        if (c.fetchone()[0] != 1):
            print('Ride with rno \'{}\' does not belong to you. Please try again.\n'.format(rno))
            continue

        break

    # Email checking
    while True:
        email = input('Enter the email of the person you want to book (creating booking)... > ').lower().strip()

        if (email == 'exit'):
            return

        # Verifies if email exists
        c.execute('SELECT COUNT(email) FROM members WHERE email = ? ;', (email,))

        if (c.fetchone()[0] != 1):
            print('The email address \'{}\' is not registered to a member. Please try again.\n'.format(email))
            continue

        break

    # Cost checking
    while True:
        cost = input('Enter the cost willing to pay per seat (creating booking)... > ').strip()

        if (cost == 'exit'):
            return

        if (len(cost) < 1):
            print('Cost cannot be empty. Please enter a valid amount.\n')
            continue

        try:
            cost = int(cost)
        except ValueError:
            print('Input is not an integer. Please try again.\n')
            continue

        break

    # Number of seats checking
    while True:
        seats = input('Enter the number of seats to be booked (creating booking)... > ').strip()
        if (seats == 'exit'):
            return

        if (len(seats) < 1):
            print('Seats cannot be empty. Please enter a valid amount.\n')
            continue

        try:
            seats = int(seats)
        except ValueError:
            print('Input is not an integer. Please try again.\n')
            continue

        break

    # Pickup location checking
    while True:
        pickup = input('Enter a pickup location lcode (creating booking): ').lower().strip()

        if (pickup == 'exit'):
            return

        # We check if the lcode exists
        c.execute('SELECT COUNT(lcode) FROM locations WHERE lower(lcode) = ?', (pickup,))

        if (c.fetchone()[0] != 1):
            print('The specified lcode does not exist. Please try again.\n')
            continue

        break

    # Dropoff location checking
    while True:
        dropoff = input('Enter a dropoff location lcode (creating booking): ').lower().strip()

        if (dropoff == 'exit'):
            return

        # We check if the lcode exists
        c.execute('SELECT COUNT(lcode) FROM locations WHERE lower(lcode) = ?', (dropoff,))

        # Output in form of (count, )
        if (c.fetchone()[0] != 1):
            print('The specified lcode does not exist. Please try again.\n')
            continue

        break

    c.execute(qGetSeats, (rno,))

    # Checking for an overbooking
    if (c.fetchone()[0] - seats < 0):

        # Prompt the user to accept an overbooking
        while True:
            print('The seats that you are trying to book exceeds the available seats, which will cause an overbooking.')
            command = input('Would you like to proceed? (y/n) > ').lower().strip()

            if (command == 'y'):
                break
            elif (command == 'n'):
                return
            else:
                print('Unknown command. Please try again.\n')
                continue

    # Get the last bno value and increment it by 1. If rid values are NULL then bno value will be 1 for the new request
    c.execute('SELECT IFNULL((MAX(bno) + 1), 1) FROM bookings ;')
    bno = c.fetchone()[0]

    # Insert the new values
    c.execute('INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?)', (bno, email, rno, cost, seats, pickup, dropoff))
    conn.commit()

    # Print success message
    print('Member booked successfully.\n')

    return

# This function allows a user to cancel a booking, provided that it is their own (they are the driver). Upon deletion, it sends a message to the user that was registered on the booking
def cancelBooking(email):

    while True:

        bno = input('Type the bno of the request which you wish to delete... > ').lower().strip()

        if (bno == 'exit'):
            return

        # Checking if bno exists
        c.execute('SELECT COUNT(bno) FROM bookings WHERE bno = ? ;', (bno,))

        if (c.fetchone()[0] < 1):
            print('Booking with bno \'{}\' does not exist. Please try again.\n'.format(bno))
            continue

        qVerify = '''

            SELECT
                COUNT(b.bno)
            FROM
                bookings AS b
            INNER JOIN
                rides AS r ON r.rno = b.rno
            WHERE
                b.bno = ?
                AND lower(r.driver) = ? ;

        '''

        c.execute(qVerify, (bno, email))

        if (c.fetchone()[0] < 1):
            print('Ride with bno \'{}\' does not belong to you. Please try again.\n'.format(bno))
            continue

        # Since bno is unique we can only have one result. In form (email, rno)
        c.execute('SELECT email, rno FROM bookings WHERE bno = ? ;', (bno,))
        memberInfo = c.fetchone()

        # Sends the appropriate message to the user that has the booking.
        c.execute('INSERT INTO inbox VALUES (?, DATETIME(\'now\'), ?, \'Your booking associated with rno {} has been deleted.\', ?, \'n\')'.format(memberInfo[1]), (memberInfo[0], email, memberInfo[1]))

        # Finally deletes the booking
        c.execute('DELETE FROM bookings WHERE bno = ? ;', (bno,))

        # Commits changes
        conn.commit()

        print('Ride with rid \'{}\' was deleted.  A message was sent to the user. Returning to requests page...\n'.format(bno))

        return

    return

##
#### Functions for posting ride requests start here (Q4) ####
##

# Gets date, pickup location, dropoff location, and amount from the user. Strips leading and trailing whitespace charcters while also making input lower case. Checks to make sure input is valid.
def postRideRequest(email):

    # Clears console and prints an intro message.
    os.system('clear||cls')
    print('This is ride request posting page. Type \'exit\' at any point to exit the posting page.\n')

    while True:

        # Date checking
        while True:
            date = input('Enter a date (creating request)... > ').lower().strip()

            if (date == 'exit'):
                return

            c.execute('SELECT DATE(?);', (date,))

            # Since a format like the following in SQLite is valid (DATE(ddddd...) where d is an integer) we check the number of dashes is exactly equal to 2 so we can avoid this.
            if (not c.fetchone()[0] or date.count('-') != 2):
                print('The date is not valid. Please try again.\n')
                continue

            break

        # Dropoff location checking
        while True:
            dropoff = input('Enter a dropoff location lcode (creating request): ').lower().strip()

            if (dropoff == 'exit'):
                return

            # We check if the lcode exists
            c.execute('SELECT COUNT(lcode) FROM locations WHERE lower(lcode) = ?', (dropoff,))

            # Output in form of (count, )
            if (c.fetchone()[0] != 1):
                print('The specified lcode does not exist. Please try again.\n')
                continue

            break

        # Pickup location checking
        while True:
            pickup = input('Enter a pickup location lcode (creating request): ').lower().strip()

            if (pickup == 'exit'):
                return

            # We check if the lcode exists
            c.execute('SELECT COUNT(lcode) FROM locations WHERE lower(lcode) = ?', (pickup,))

            if (c.fetchone()[0] != 1):
                print('The specified lcode does not exist. Please try again.\n')
                continue

            break


        while True:
            amount = input('Amount willing to pay per seat: ').strip()

            if (amount=='exit'):
                return

            if (len(amount) < 1):
                print('Amount cannot be empty. Please enter a valid amount.\n')
                continue

            try:
                amount = int(amount)
            except ValueError:
                print('Input is not an integer. Please try again.\n')
                continue

            break

        # Get the last rid value and increment it by 1. If rid values are NULL then rid value will be 1 for the new request
        c.execute('SELECT IFNULL((MAX(rid) + 1), 1) FROM requests ;')

        # Insert the new values
        c.execute('INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?)', (c.fetchone()[0], email, date, pickup, dropoff, amount))
        conn.commit()

        # Print success message
        print('Request posted successfully.\n')

    return

##
#### Functions for searching and deleting rides start here (Q5) ####
##

# This function is the main control loop for ride requests. It allows the user to display, delete, orfind requests that mathc a location string.
def requestsPage(email):

    while True:

        os.system('clear||cls')

        print('You are now viewing your requests. Type \'display\' to display your requests, \'delete\' to delete a request, or \'location\' to view requests that depart from a specific location. Type \'exit\' at any time to return to the main menu.\n')

        while True:

            command = input('Enter a command... > ').lower().strip()

            if (command == 'exit'):
                return
            elif (command == 'display'):
                displayRequests(email)
                continue
            elif (command == 'delete'):
                deleteRequest(email)
                continue
            elif (command == 'location'):
                requestsLocations(email)
                break
            else:
                print('Unrecognized command. Valid commands are \'display\', \'delete\', \'location\', and \'exit\'.')
                continue

    return

# This function gets all requests from the user matching an lcode or city exactly. Calls resultsWizard().
def requestsLocations(email):

    qSearchLocations = '''

        SELECT
            r.*
        FROM
            requests AS r
        INNER JOIN
            locations AS l ON l.lcode = r.pickup
        WHERE
            lower(l.lcode) = :keyword
            OR lower(l.city) = :keyword ;

    '''

    print()

    while True:

        locKeyword = input('Please specify a location code or a city name... > ').lower().strip()

        if (locKeyword == 'exit'):
            return

        # Finding locations (lcode, city) that match the keyword
        c.execute(qSearchLocations, {'keyword':locKeyword})
        results = c.fetchall()

        # If there is nothing in the result set, complain.
        if (not results):
            print('No locations found for \'{}\'. Please try again.\n'.format(locKeyword))
            continue

        # Otherwise, display results
        print('\nDisplaying results. At any point, you can type \'message\' to message a member of a specific request.')

        formatString = '    {:<13}  {:<15}  {:<11}  {:<10}  {:<10}  {:<10}'
        print(formatString.format(*'Request ID, Email, Date, Pickup, Dropoff, Amount'.split(', ')))

        resultsWizard(email, results, formatString, requestsHelper)

    return

# helper function for above meant to be passed into resultsWizard().
def requestsHelper(email, _):

    while True:

        command = input('Type \'more\' to see more results or type a command... > ').lower().strip()

        if (command == 'message'):
            requestsMessage(email)
            continue
        elif (command == 'more'):
            return True
        elif (command == 'exit'):
            return
        else:
            print('Unrecognized command. Valid commands are \'more\', \'message\', and \'exit\'.')

    return

# Small function that displays the requests of the user.
def displayRequests(email):

    # Get all of the member's requests
    c.execute('SELECT * FROM requests WHERE lower(email) = ?;',(email,))

    results = c.fetchall()

    # Check if the user has requests
    if (len(results) == 0):
        print('You have no requests.\n')
        return

    print('Requests for \'{}\':'.format(email))

    formatString = '    {:<9}  {:<15}  {:<13}  {:<9}  {:<9}  {:<7}'

    # Print table headers
    print(formatString.format(*'Ride ID, Email, Date, Pickup, Dropoff, Amount'.split(', ')))

    fixedResults = fixResults(results)

    for r in fixedResults:
        print(formatString.format(*r))

# Prompts the user to delete a request based on rid and their email. It won't let them delete a request that does not belong to them
def deleteRequest(email):

    while True:

        rid = input('Type the rid of the request which you want to delete... > ').lower().strip()

        if (rid == 'exit'):
            return

        c.execute('SELECT COUNT(rid) FROM requests WHERE rid = ? ;', (rid,))

        if (c.fetchone()[0] < 1):
            print('Ride with rid \'{}\' does not exist. Please try again.\n'.format(rid))
            continue

        c.execute('SELECT COUNT(rid) FROM requests WHERE rid = ? AND email = ?;', (rid, email))

        if (c.fetchone()[0] < 1):
            print('Ride with rid \'{}\' does not belong to you. Please try again.\n'.format(rid))
            continue

        c.execute('DELETE FROM requests WHERE rid = ? AND lower(email) = ?;', (rid, email))
        conn.commit()

        print('Ride with rid \'{}\' was deleted. Returning to requests page...\n'.format(rid))
        return

# Small function for handling input for the search "engine" above. Returns True if the user requests more results, and None if the user wants to exit. For sending a message, we call sendMessageHelper()
def requestsMessage(email):

    print()

    while True:

        rid = input('Please type the ride number (rid) of the ride you want to send a message to or type \'exit\' to return to search... > ').lower().strip()

        if (rid == 'exit'):
            return

        if (len(rid) < 1):
            print('Request ID cannot be empty. Please try again.\n')
            continue

        try:
            rid = int(rid)
        except ValueError:
            print('Input is not an integer. Please try again.\n')
            continue

        # Check existence of a request and print appropriate message if it does not.
        c.execute('SELECT email FROM requests WHERE rid = ?', (rid,))

        # In form of ('requester',) or None
        requester = c.fetchone()

        # This checks if the rid of that ride exists and grabs the requester.
        if (not requester):
            print('The request id you specified does not exist. Please try again.\n')
            continue

        message = input('Type the message you want to send to \'{}\'... > '.format(requester[0]))

        if (message == 'exit'):
            return

        c.execute('INSERT INTO inbox VALUES (?, DATETIME(\'now\'), ?, ?, NULL, \'n\')', (requester[0], email, message))
        conn.commit()

        print('Message sent.\n')

        return

##
#### Generic Functions start here ####
##

# This is a highly specialized function whose main purpose is to display a X number of results 5 at a time. We need the email of the currently logged in user to pass to the helperfunction. We need a pointer to a function (helperFunction) which is the main controller for the 'more' commands, etc. We also need the list of results. Finally, we need a format string that matches the result set to print it nicely. It might be a bit of a weird way of doing things, but I found it to be helpful.
def resultsWizard(email, results, formatString, helperFunction, hfParam = None):
    exitCode = False
    i = 0

    while (exitCode == False):
        try:
            # Makes it so it prints five results the first time.
            if (i == 0):
                showFiveResults(formatString, results)
                continue

            # We call the command handler for its specified function.
            helperReturn = helperFunction(email, hfParam)

            # If helperFunction returns True, this means that we must show five results.
            if (helperReturn == True):
                showFiveResults(formatString, results[i:])

            # Returning False indicates that it is a special case, namely we have to propogate that case up the chain.
            elif (helperReturn == False):
                return False

            # If searchRideHelper() returns None, then we have been instructed to exit.
            else:
                exitCode = True

        except IndexError:
            print('No more results to show.')

        finally:
            i += 5

    return

# Attempts to print five results on the screen. We need a format string that matches the elements of result. We expect at some point for this function to run into an IndexError, which we catch in the caller.
def showFiveResults(formatString, results):

    fixedResults = fixResults(results)

    # Actually print the values. We use the star operator to unpack all the results so we can pass those as arguments in .format().
    for i in range(0, 5):
        print(formatString.format(*fixedResults[i]))

    return

# The point of fixResults is to allow for the printing of NULL values. Since .format() doesn't like NULLs in the format string we must do element or 'NULL' so that if element is None (NULL in SQL) then it would replace the None with the literal string 'NULL'.
def fixResults(results):

    fixedResults = []

    for result in results:
        temp = []

        for element in result:
            temp.append(element or 'NULL')

        fixedResults.append(temp)

    return fixedResults

# Calling main with the system arguments. Gives all arguments after the first arguments specified by sys.argv, which is just the file path. To be clar, we don't need that
main( len(sys.argv[1:]), sys.argv[1:] )
