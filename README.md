# Clockzy

![Status](https://img.shields.io/badge/Version-1.0-blue.svg)
![Status](https://img.shields.io/badge/Status-stable-green.svg)

Slack application that allows users to keep track of their working hours and history through slack commands.

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_logo.png">
</p>

- [Clockzy](#clockzy)
- [Introduction](#introduction)
- [How to use](#how-to-use)
  * [Considerations before starting](#considerations-before-starting)
  * [Create your user](#create-your-user)
  * [Clock your actions](#clock-your-actions)
  * [Check your worked time](#check-your-worked-time)
  * [Check your worked time history](#check-your-worked-time-history)
  * [Check your clock history](#check-your-clock-history)
  * [Check your today info](#check-your-today-info)
  * [Check the availability of another user](#check-the-availability-of-another-user)
  * [Create an username alias](#create-an-username-alias)
  * [Check the aliases already created](#check-the-aliases-already-created)
  * [Link your account to the Intratime app](#link-your-account-to-the-intratime-app)
  * [Unlink your Intratime account](#unlink-your-intratime-account)
  * [Update your user information](#update-your-user-information)
  * [Delete your user](#delete-your-user)
  * [Get commands help](#get-commands-help)
- [How to deploy](#how-to-deploy)
  * [Configure your slack app](#configure-your-slack-app)
  * [Configure your app settings](#configure-your-app-settings)
  * [Run the app](#run-the-app)
- [Contributions](#contributions)

# Introduction

_Clockzy_ app is an application that allows to keep an individual time control in a very comfortable way.

Users will be able to record different actions (entry, pause, return and out) to later make queries on the time worked,
history ... and even know if other colleagues are available at that time.

In addition, it offers the possibility of integrating these clockings with the [Intratime](https://www.intratime.es/)
application.

In short, this application offers the following capabilities:

- Clock your entry, pause, return or out action.
- Get your total worked time (clocked).
- Get your clock history.
- Get your worked time history.
- Check if other users of the application are active at that moment.

---

# How to use

## Considerations before starting

- All messages generated as a result of any command are of **private visibility**, thus avoiding flooding public
conversations and preventing the rest of the users from seeing your information or actions.

- If you link your user to an intratime account, the **password is stored in encrypted form**.

- The _clockzy_ app will **only deal with requests made by slack**, using a signature key. This prevents
unwanted access in external applications.

## Create your user

Create your user by simply typing `/sign-up` in the chat of any slack channel (not threads)


<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_user_created.png">
</p>

> Note: You do not need to enter any data, since will be used your slack profile data.

## Clock your actions

Once the user is registered (you only need to do it once), you can clock your action (_IN_, _PAUSE_, _RETURN_ or _OUT_)
in the intratime application using:

```
/clock <action>
```

**Allowed parameters**: `in`, `pause`, `return`, `out`.

If the action is successful, the following message will be displayed:

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_clock_example.png">
</p>

If you have linked your user with your account in [Intratime](https://www.intratime.es/), then the icon on the right
representing the action will be orange.

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_clock_example_2.png">
</p>

This functionality also filters out possible inconsistent clockings, such as trying to clock a `RETURN` without a
previous `PAUSE` ... In this case, we can see messages like the following:

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_clock_error.png">
</p>

## Check your worked time

Check how long you have been working, making the calculation based on the clockings you have made. You can get this
calculation for today, week or month, using:

```
/time <time_range>
```

**Allowed parameters**: `today`, `week`, `month`.


<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_time.png">
</p>


In addition, it has an icon that will change color depending on the number of hours you have been working:
- :green_circle: You have already completed the required time (`[0h, 7h)`)
- :yellow_circle: You are close to meet the required time (`[7h, 8h)`)
- :red_circle: You are still some time away from the required time (`[8h, )`)

## Check your worked time history

Get the worked time history that you have done during a period of time, using:

```
/time-history <time_range>
```

**Allowed parameters**: `today`, `week`, `month`.

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_time_history.png">
</p>

> Note: There will also be a color indicator according to the average time.


## Check your clock history


Check all the clockings that you have made in a period of time, using:


```
/clock-history <time_range>
```

**Allowed parameters**: `today`, `week`, `month`.

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_clock_history.png">
</p>

> Note: There will also be a color indicator according to the average and total time.


## Check your today info

Check the time worked and actions recorded for today with a simple command. To do this use:

```
/today
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_today.png">
</p>

> Note: There will also be a color indicator according to the total time.

## Check the availability of another user

To check if another user is currently available (based on the last registered action), use the following command:

```
/check <username or alias>
```

<p>
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_check_available.png">
</p>

<p>
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_check_absent.png">
</p>


<p>
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_check_no_available.png">
</p>


It can be difficult to know the exact user name, so **you can create a specific alias for that user, and perform the check using that alias**.

## Create an username alias

To facilitate the availability query on users, it is possible to create a specific alias to perform this query. You can
create an alias with the following command:

```
/alias <username> <alias>
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_add_alias.png">
</p>

For example, let's create an alias called `jonathan_qa` for the `jmv74211` username.

```
/alias jmv74211 jonathan_qa
```

From now on, we can query the user's status using that alias:

```
/check
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_alias_check.png">
</p>

## Check the aliases already created

You can query the previously created aliases with the following command:

```
/get-aliases
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_get_aliases.png">
</p>

## Link your account to the Intratime app

It is possible to link the clockings made in the clockzy application with the [Intratime](https://www.intratime.es/)
application. All clockings will be performed in both apps.

By default it is disabled. To link your account, run the following command:

```
/enable-intratime <intratime_email_account> <intratime_password>
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_enable_intratime.png">
</p>

> Note: The intratime password will be saved in a encrypted form.

> Note: If you ever modify your Intratime account credentials, you can re-run this command to update your credentials in the clockzy app.

## Unlink your Intratime account

If for any reason you want to unlink the synchronization with [Intratime](https://www.intratime.es/), you can do so
using the following command:

```
/disable-intratime
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_disable_intratime.png">
</p>

> Note: Your credentials will be deleted from the clockzy app database.

## Update your user information

Your user information is collected from slack at the time of user creation. If you ever change your **timezone** or
**username**, run the following command to update that information in the clockzy app.

```
/update-user
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_update_user.png">
</p>

## Delete your user

If for any reason you want to delete your clockzy app user, you can do it with the following command:

```
/delete-user
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_delete_user.png">
</p>

> Note: All the information related to your user will be deleted: profile, clockings...

## Get commands help

To display the set of available commands and their help menu run the following command:

```
/help
```

<p align="center">
    <img src="https://raw.githubusercontent.com/jmv74211/tools/master/images/repository/clockzy/clockzy_help.png">
</p>

---

# How to deploy

## Configure your slack app

First you will have to create a slack application. You can create one from this website
[https://api.slack.com/](https://api.slack.com/).

**Get slack app credentials**

Once created, you will have to obtain your **app tokens**. You can find it in `OAuth & Permissions section`.
In this case, it is only necessary to get the `Bot User OAuth Token`. It will have a format like the following:

_Bot User OAuth Token_
```
xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

It will also be necessary to obtain the **signing secret key** to verify that the requests come from our slack app. You
can find this key in _Basic information_ section.

**Set your token scopes**

It is necessary to define the scope of permissions that our slack application will have. You can configure them in `OAuth & Permissions` section in the slack app configuration. The needed token scopes are as follows:

- **Bot token scopes**: `commands`, `users:read`.

**Define your commands**

Commands enable users to interact with your app from within Slack. In this case, we have to define the following
commands in the slack app configuration:

- `/sign-up`: _https://<domain_name>/sign-up_
- `/delete-user`: _https://<domain_name>/delete-user_
- `/update-user`: _https://<domain_name>/update-user_
- `/clock`: _https://<domain_name>/clock_
- `/time`: _https://<domain_name>/time_
- `/clock-history`: _https://<domain_name>/clock-history_
- `/time-history`: _https://<domain_name>/time-history_
- `/today`: _https://<domain_name>/today_
- `/help`: _https://<domain_name>/help_
- `/alias`: _https://<domain_name>/alias_
- `/get-aliases`: _https://<domain_name>/get-aliases_
- `/check`: _https://<domain_name>/check_
- `/enable-intratime`: _https://<domain_name>/enable-intratime_
- `/disable-intratime`: _https://<domain_name>/disable-intratime_

## Configure your app settings

You have to configure the `clockzy` application modifying the
[settings.py](https://github.com/jmv74211/clockzy/blob/master/src/clockzy/config/settings.py)
file.

In addition, you have to update the [.env](https://github.com/jmv74211/clockzy/blob/master/.env) file
to enter your `MYSQL_ROOT_PASSWORD` credentials.

In case of modifying default ports ..., take a look at the
[docker-compose.yaml](https://github.com/jmv74211/clockzy/blob/master/docker-compose.yaml) file
and update to your new values.

## Run the app

Once the application is configured (see the previous steps), Running the application is very simple, you just need
to have installed [docker](https://www.docker.com/get-started) and
[docker-compose](https://docs.docker.com/compose/install/), and execute the following command in root directory.

```bash
docker-compose up
```

All services will be automatically started.

---

# Contributions

Any doubt or suggestion, you can create issues and/or make pull requests :)
