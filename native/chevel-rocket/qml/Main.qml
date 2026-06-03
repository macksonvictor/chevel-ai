import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: root

    x: 80
    y: 80
    width: 1440
    height: 900
    minimumWidth: 1280
    minimumHeight: 720
    visible: true
    visibility: Window.Windowed
    color: "#080A0D"
    title: "Chevel Rocket"

    property int currentTab: 0
    property string currentTimeText: Qt.formatTime(new Date(), "HH:mm:ss")
    property string pendingMethod: ""
    readonly property var tabs: [
        "Mission Control",
        "Robot Control",
        "Computer Control",
        "Safety",
        "Voice",
        "Logs",
        "UI Kit"
    ]

    Component.onCompleted: {
        root.visible = true
        root.raise()
        root.requestActivate()
        console.log("Chevel Rocket interface loaded")
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: root.currentTimeText = Qt.formatTime(new Date(), "HH:mm:ss")
    }

    function openCritical(name, message, methodName) {
        pendingMethod = methodName
        confirmModal.openFor(name, message, true)
    }

    function executePending() {
        if (pendingMethod === "armRobot")
            robotController.armRobot()
        else if (pendingMethod === "startMission")
            robotController.startMission()
        else if (pendingMethod === "rebootSystem")
            robotController.rebootSystem()
        else if (pendingMethod === "emergencyStop")
            robotController.emergencyStop()

        pendingMethod = ""
    }

    component PanelTitle: Text {
        color: "#E8EAED"
        font.pixelSize: 16
        font.bold: true
        elide: Text.ElideRight
    }

    component MutedText: Text {
        color: "#9AA3AF"
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }

    component SectionPanel: Rectangle {
        id: panel
        default property alias contentData: body.data

        radius: 8
        color: "#12161D"
        border.width: 1
        border.color: "#2A313B"
        clip: true

        ColumnLayout {
            id: body
            anchors.fill: parent
            anchors.margins: 14
            spacing: 10
        }
    }

    background: Rectangle {
        anchors.fill: parent
        color: "#080A0D"

        Canvas {
            anchors.fill: parent
            opacity: 0.16

            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = "#1C2530"
                ctx.lineWidth = 1

                for (var x = 0; x < width; x += 32) {
                    ctx.beginPath()
                    ctx.moveTo(x, 0)
                    ctx.lineTo(x, height)
                    ctx.stroke()
                }

                for (var y = 0; y < height; y += 32) {
                    ctx.beginPath()
                    ctx.moveTo(0, y)
                    ctx.lineTo(width, y)
                    ctx.stroke()
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 112
            radius: 8
            color: "#0E1116"
            border.width: 1
            border.color: "#2A313B"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 16

                Image {
                    source: "assets/ui/branding/chevel-rocket-logo.png"
                    Layout.preferredWidth: 286
                    Layout.preferredHeight: 84
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                }

                ColumnLayout {
                    spacing: 4
                    Layout.preferredWidth: 275

                    Text {
                        text: "Chevel Rocket"
                        color: "#E8EAED"
                        font.pixelSize: 25
                        font.bold: true
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    Text {
                        text: "Mission & Robot Control"
                        color: "#9AA3AF"
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    Text {
                        text: "Chevel AI native executor for Dum-E"
                        color: "#22D3EE"
                        opacity: 0.78
                        font.pixelSize: 11
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                }

                RocketStatusPill {
                    label: "MODE"
                    valueText: "SIMULATED"
                    status: "SIMULATED"
                    Layout.preferredWidth: 190
                }

                RocketSegmentedToggle {
                    segments: ["SIMULATION", "LIVE"]
                    selectedIndex: 0
                    interactive: false
                    Layout.preferredWidth: 244
                    Layout.preferredHeight: 38
                }

                Item { Layout.fillWidth: true }

                RocketStatusPill {
                    label: "MODEL"
                    valueText: "Llama/local model"
                    status: "OK"
                    Layout.preferredWidth: 220
                }

                Rectangle {
                    Layout.preferredWidth: 150
                    Layout.preferredHeight: 42
                    radius: 7
                    color: "#151A21"
                    border.width: 1
                    border.color: "#2A313B"

                    Text {
                        anchors.centerIn: parent
                        text: root.currentTimeText
                        color: "#E8EAED"
                        font.pixelSize: 20
                        font.family: "Consolas"
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 230
                Layout.fillHeight: true
                radius: 8
                color: "#0E1116"
                border.width: 1
                border.color: "#2A313B"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    Repeater {
                        model: root.tabs

                        RocketTabButton {
                            required property int index
                            required property string modelData

                            text: modelData
                            current: root.currentTab === index
                            Layout.fillWidth: true
                            onClicked: root.currentTab = index
                        }
                    }

                    Item { Layout.fillHeight: true }

                    RocketStatusPill {
                        valueText: "SAFE MODE"
                        status: "SAFE MODE"
                        iconText: "\u2713"
                        Layout.fillWidth: true
                    }

                    RocketDangerButton {
                        text: "EMERGENCY STOP"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 86
                        locked: robotController.emergencyActive
                        onClicked: root.openCritical("EMERGENCY STOP",
                                                     "This engages the simulated emergency stop. No real hardware is connected. Type CONFIRMAR to continue.",
                                                     "emergencyStop")
                    }
                }
            }

            StackLayout {
                currentIndex: root.currentTab
                Layout.fillWidth: true
                Layout.fillHeight: true

                ScrollView {
                    id: missionScroll
                    clip: true

                    ColumnLayout {
                        width: missionScroll.availableWidth
                        spacing: 12

                        PanelTitle { text: "Mission Control" }
                        MutedText { text: "Mock mission deck for Dum-E. All actions stay inside Chevel Rocket simulation." }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 245
                            spacing: 12

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Current Mission" }
                                MutedText { text: "Mission: Warehouse inspection route / simulated" }

                                RocketStatusPill {
                                    valueText: robotController.armed ? "READY" : "WARNING"
                                    status: robotController.armed ? "READY" : "WARNING"
                                    Layout.preferredWidth: 170
                                }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    rowSpacing: 8
                                    columnSpacing: 12

                                    MutedText { text: "Queue"; Layout.preferredWidth: 110 }
                                    Text { text: "3 mock missions"; color: "#E8EAED"; font.pixelSize: 13 }
                                    MutedText { text: "Risk"; Layout.preferredWidth: 110 }
                                    Text { text: robotController.missionRisk + "%"; color: robotController.missionRisk > 70 ? "#EF4444" : "#F59E0B"; font.pixelSize: 13; font.bold: true }
                                    MutedText { text: "Executor"; Layout.preferredWidth: 110 }
                                    Text { text: "Chevel AI / Llama local"; color: "#E8EAED"; font.pixelSize: 13 }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10

                                    RocketButton {
                                        text: "START MISSION"
                                        iconText: "\u25b6"
                                        variant: "primary"
                                        locked: robotController.emergencyActive || !robotController.armed
                                        Layout.fillWidth: true
                                        onClicked: root.openCritical("START MISSION",
                                                                     "This starts a simulated mission profile only. Type CONFIRMAR to continue.",
                                                                     "startMission")
                                    }

                                    RocketButton {
                                        text: "PAUSE MISSION"
                                        iconText: "||"
                                        variant: "secondary"
                                        locked: robotController.emergencyActive
                                        Layout.fillWidth: true
                                        onClicked: robotController.pauseMission()
                                    }

                                    RocketDialogButton {
                                        role: "warning"
                                        text: "RETURN HOME"
                                        locked: robotController.emergencyActive
                                        Layout.fillWidth: true
                                        onClicked: robotController.returnHome()
                                    }
                                }
                            }

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Mission Actions" }
                                MutedText { text: "Human confirmation is required before critical simulated operations." }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10

                                    RocketDialogButton { role: "confirm"; text: "CONFIRM"; Layout.fillWidth: true; onClicked: root.openCritical("MISSION CONFIRM", "Confirm the queued simulated mission step. Type CONFIRMAR to continue.", "") }
                                    RocketDialogButton { role: "cancel"; text: "CANCEL"; Layout.fillWidth: true; onClicked: robotController.pauseMission() }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10

                                    RocketDialogButton { role: "ready"; text: "READY"; Layout.fillWidth: true }
                                    RocketDialogButton { role: "warning"; text: "WARNING"; Layout.fillWidth: true }
                                }

                                Repeater {
                                    model: ["Dock scan / pending", "Aisle route / ready", "Return checkpoint / blocked until confirm"]

                                    Rectangle {
                                        required property string modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 34
                                        radius: 6
                                        color: "#151A21"
                                        border.width: 1
                                        border.color: "#2A313B"

                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            anchors.left: parent.left
                                            anchors.leftMargin: 12
                                            text: modelData
                                            color: "#E8EAED"
                                            font.pixelSize: 12
                                        }
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 240
                            spacing: 12

                            Gauge { title: "Mission Risk"; value: robotController.missionRisk; minValue: 0; maxValue: 100; unit: "%"; warningThreshold: 45; dangerThreshold: 75; Layout.fillWidth: true; Layout.fillHeight: true }
                            Gauge { title: "Battery"; value: robotController.batteryLevel; minValue: 0; maxValue: 100; unit: "%"; warningThreshold: 35; dangerThreshold: 18; dangerBelow: true; Layout.fillWidth: true; Layout.fillHeight: true }
                            Gauge { title: "Signal"; value: robotController.signalStrength; minValue: 0; maxValue: 100; unit: "%"; warningThreshold: 45; dangerThreshold: 25; dangerBelow: true; Layout.fillWidth: true; Layout.fillHeight: true }
                        }
                    }
                }

                ScrollView {
                    id: robotScroll
                    clip: true

                    ColumnLayout {
                        width: robotScroll.availableWidth
                        spacing: 12

                        PanelTitle { text: "Robot Control" }
                        MutedText { text: "Dum-E simulated robot controls. Motors, sensors and camera are mock/offline only." }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 295
                            spacing: 12

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Dum-E Command Rail" }

                                RocketButton {
                                    text: "ARM ROBOT"
                                    iconText: "\u25c7"
                                    variant: "primary"
                                    locked: robotController.emergencyActive || robotController.armed
                                    Layout.fillWidth: true
                                    onClicked: root.openCritical("ARM ROBOT", "Arm Dum-E inside simulation only. Type CONFIRMAR to continue.", "armRobot")
                                }

                                RocketButton {
                                    text: "DISARM ROBOT"
                                    iconText: "\u00d7"
                                    variant: robotController.armed ? "secondary" : "disabled"
                                    locked: robotController.emergencyActive || !robotController.armed
                                    Layout.fillWidth: true
                                    onClicked: robotController.disarmRobot()
                                }

                                RocketButton {
                                    text: "CALIBRATE SENSORS"
                                    iconText: "\u25ce"
                                    variant: "outlined"
                                    locked: robotController.emergencyActive
                                    Layout.fillWidth: true
                                    onClicked: robotController.calibrateSensors()
                                }

                                RocketDialogButton {
                                    role: "warning"
                                    text: "REBOOT SYSTEM"
                                    locked: robotController.emergencyActive
                                    Layout.fillWidth: true
                                    onClicked: root.openCritical("REBOOT SYSTEM", "This performs a simulated controller reboot. Type CONFIRMAR to continue.", "rebootSystem")
                                }
                            }

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Robot Status" }

                                RocketStatusPill { label: "Robot"; valueText: robotController.armed ? "ONLINE" : "OFFLINE"; status: robotController.armed ? "ONLINE" : "OFFLINE"; Layout.fillWidth: true }
                                RocketStatusPill { label: "Motors"; valueText: robotController.motorTemperature > 70 ? "WARNING" : "READY"; status: robotController.motorTemperature > 70 ? "WARNING" : "READY"; Layout.fillWidth: true }
                                RocketStatusPill { label: "Sensors"; valueText: robotController.emergencyActive ? "OFFLINE" : "READY"; status: robotController.emergencyActive ? "OFFLINE" : "READY"; Layout.fillWidth: true }
                                RocketStatusPill { label: "Camera"; valueText: "OFFLINE"; status: "OFFLINE"; Layout.fillWidth: true }

                                TelemetryPanel {
                                    controller: robotController
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 230
                            spacing: 12

                            Gauge { title: "Motor Temp"; value: robotController.motorTemperature; minValue: 0; maxValue: 120; unit: "C"; warningThreshold: 70; dangerThreshold: 90; Layout.fillWidth: true; Layout.fillHeight: true }
                            Gauge { title: "Speed"; value: robotController.speed; minValue: 0; maxValue: 5; unit: "m/s"; warningThreshold: 3.4; dangerThreshold: 4.4; Layout.fillWidth: true; Layout.fillHeight: true }
                            Gauge { title: "CPU Load"; value: robotController.cpuLoad; minValue: 0; maxValue: 100; unit: "%"; warningThreshold: 70; dangerThreshold: 90; Layout.fillWidth: true; Layout.fillHeight: true }
                        }
                    }
                }

                ScrollView {
                    id: computerScroll
                    clip: true

                    ColumnLayout {
                        width: computerScroll.availableWidth
                        spacing: 12

                        PanelTitle { text: "Computer Control" }
                        MutedText { text: "Local command preview for Chevel AI. No terminal command is executed from this interface." }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 315
                            spacing: 12

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Simulated Command Preview" }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    radius: 7
                                    color: "#080A0D"
                                    border.width: 1
                                    border.color: "#2A313B"

                                    Text {
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        text: "chevel-ai --module rocket --robot Dum-E --mode simulate\\nmodel: Llama/local model\\nrisk: medium\\nexecution: blocked until human confirm"
                                        color: "#9AA3AF"
                                        font.family: "Consolas"
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10

                                    RocketButton { text: "START MISSION"; iconText: "\u25b6"; variant: "primary"; Layout.fillWidth: true; onClicked: root.openCritical("SIMULATED COMMAND", "Confirm the simulated command preview. No terminal will be executed. Type CONFIRMAR to continue.", "") }
                                    RocketButton { text: "PAUSE MISSION"; iconText: "||"; variant: "secondary"; Layout.fillWidth: true }
                                }
                            }

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Command Gate" }
                                RocketStatusPill { label: "Risk"; valueText: "WARNING"; status: "WARNING"; Layout.fillWidth: true }
                                RocketStatusPill { label: "Gate"; valueText: "READY"; status: "READY"; Layout.fillWidth: true }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    RocketDialogButton { role: "confirm"; text: "CONFIRM"; Layout.fillWidth: true; onClicked: root.openCritical("COMMAND CONFIRM", "Confirm mock command routing only. Type CONFIRMAR to continue.", "") }
                                    RocketDialogButton { role: "cancel"; text: "CANCEL"; Layout.fillWidth: true }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    RocketDialogButton { role: "warning"; text: "WARNING"; Layout.fillWidth: true }
                                    RocketDialogButton { role: "ready"; text: "READY"; Layout.fillWidth: true }
                                }
                            }
                        }
                    }
                }

                ScrollView {
                    id: safetyScroll
                    clip: true

                    ColumnLayout {
                        width: safetyScroll.availableWidth
                        spacing: 12

                        PanelTitle { text: "Safety" }
                        MutedText { text: "Critical actions are blocked behind human confirmation. No real hardware is connected." }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 305
                            spacing: 12

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Critical Safety" }

                                RocketDangerButton {
                                    text: "EMERGENCY STOP"
                                    locked: robotController.emergencyActive
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 96
                                    onClicked: root.openCritical("EMERGENCY STOP",
                                                                 "This engages the simulated emergency stop and blocks all mock commands. Type CONFIRMAR to continue.",
                                                                 "emergencyStop")
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    RocketDialogButton { role: "cancel"; text: "CANCEL"; Layout.fillWidth: true }
                                    RocketDialogButton { role: "confirm"; text: "CONFIRM"; Layout.fillWidth: true; onClicked: root.openCritical("SAFETY CONFIRM", "Confirm safe-mode simulation only. Type CONFIRMAR to continue.", "") }
                                }

                                RocketDialogButton {
                                    role: "ready"
                                    text: "CLEAR EMERGENCY"
                                    visible: robotController.emergencyActive
                                    Layout.fillWidth: true
                                    onClicked: robotController.clearEmergency()
                                }
                            }

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Safety State" }
                                RocketStatusPill { valueText: "SAFE MODE"; status: "SAFE MODE"; iconText: "\u2713"; Layout.fillWidth: true }
                                RocketStatusPill { valueText: robotController.emergencyActive ? "WARNING" : "READY"; status: robotController.emergencyActive ? "WARNING" : "READY"; Layout.fillWidth: true }
                                RocketStatusPill { valueText: robotController.emergencyActive ? "OFFLINE" : "ONLINE"; status: robotController.emergencyActive ? "OFFLINE" : "ONLINE"; Layout.fillWidth: true }
                                MutedText { text: "Acoes criticas bloqueadas ate confirmacao humana. Estado persistente apenas nesta simulacao." }
                            }
                        }
                    }
                }

                ScrollView {
                    id: voiceScroll
                    clip: true

                    ColumnLayout {
                        width: voiceScroll.availableWidth
                        spacing: 12

                        PanelTitle { text: "Voice" }
                        MutedText { text: "Voice pipeline mock for Chevel AI. Wake word: Chevel. STT/TTS stay offline/mock." }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 300
                            spacing: 12

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Voice Pipeline" }
                                RocketSegmentedToggle { segments: ["SIMULATION", "LIVE"]; selectedIndex: 0; interactive: false; Layout.preferredWidth: 260 }
                                RocketStatusPill { label: "Wake"; valueText: "Chevel"; status: "READY"; Layout.fillWidth: true }
                                RocketStatusPill { label: "STT"; valueText: "OFFLINE"; status: "OFFLINE"; Layout.fillWidth: true }
                                RocketStatusPill { label: "TTS"; valueText: "OFFLINE"; status: "OFFLINE"; Layout.fillWidth: true }
                            }

                            SectionPanel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PanelTitle { text: "Audio Devices" }
                                RocketStatusPill { label: "Mic"; valueText: "OFFLINE"; status: "OFFLINE"; Layout.fillWidth: true }
                                RocketStatusPill { label: "Speaker"; valueText: "OFFLINE"; status: "OFFLINE"; Layout.fillWidth: true }
                                RocketStatusPill { label: "Model"; valueText: "Llama/local model"; status: "READY"; Layout.fillWidth: true }
                                RocketDialogButton { role: "warning"; text: "WARNING"; Layout.fillWidth: true }
                                RocketDialogButton { role: "ready"; text: "READY"; Layout.fillWidth: true }
                            }
                        }
                    }
                }

                ScrollView {
                    id: logsScroll
                    clip: true

                    ColumnLayout {
                        width: logsScroll.availableWidth
                        spacing: 12

                        PanelTitle { text: "Logs" }
                        MutedText { text: "Live mock event stream from Chevel Rocket simulation." }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            RocketStatusPill { label: "Source"; valueText: "SIMULATED"; status: "SIMULATED"; Layout.preferredWidth: 200 }
                            RocketStatusPill { label: "Robot"; valueText: "Dum-E"; status: "READY"; Layout.preferredWidth: 180 }
                            RocketDialogButton { role: "warning"; text: "WARNING"; Layout.preferredWidth: 170 }
                            RocketDialogButton { role: "ready"; text: "READY"; Layout.preferredWidth: 150 }
                        }

                        LogConsole {
                            logs: robotController.logs
                            Layout.fillWidth: true
                            Layout.preferredHeight: 520
                        }
                    }
                }

                RocketButtonGallery {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
            }
        }
    }

    ConfirmModal {
        id: confirmModal
        onConfirmed: root.executePending()
    }
}
