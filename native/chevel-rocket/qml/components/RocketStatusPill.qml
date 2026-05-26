import QtQuick
import QtQuick.Layouts

Item {
    id: root

    property string label: ""
    property string status: "OK"
    property string valueText: status
    property string iconText: ""

    implicitHeight: 32
    implicitWidth: 190

    function statusTone() {
        if (status === "OK" || status === "CONNECTED" || status === "ONLINE" || status === "READY" || status === "SAFE MODE")
            return "ready"
        if (status === "WARNING" || status === "SIMULATED")
            return "warning"
        if (status === "ERROR" || status === "EMERGENCY")
            return "danger"
        return "offline"
    }

    function accentColor() {
        var t = statusTone()
        if (t === "ready")
            return "#22C55E"
        if (t === "warning")
            return "#F59E0B"
        if (t === "danger")
            return "#EF4444"
        return "#9AA3AF"
    }

    function fillColor() {
        var t = statusTone()
        if (t === "ready")
            return "#111D14"
        if (t === "warning")
            return "#211B10"
        if (t === "danger")
            return "#251318"
        return "#151A21"
    }

    Rectangle {
        anchors.fill: parent
        radius: 9
        color: root.fillColor()
        border.width: 1
        border.color: root.accentColor()
        opacity: 0.96

        Rectangle {
            anchors.fill: parent
            anchors.margins: 3
            radius: 7
            color: "transparent"
            border.width: 1
            border.color: root.accentColor()
            opacity: 0.12
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            spacing: 8

            Text {
                visible: root.iconText.length > 0
                text: root.iconText
                color: root.accentColor()
                font.pixelSize: 14
                font.bold: true
            }

            Text {
                text: root.label
                color: "#9AA3AF"
                font.pixelSize: 11
                font.bold: true
                visible: root.label.length > 0
                Layout.preferredWidth: visible ? 58 : 0
                elide: Text.ElideRight
            }

            Text {
                text: root.valueText
                color: root.accentColor()
                font.pixelSize: 12
                font.bold: true
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            Rectangle {
                Layout.preferredWidth: 8
                Layout.preferredHeight: 8
                radius: 4
                color: root.accentColor()
                opacity: 0.88
            }
        }
    }
}
