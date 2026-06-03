import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root

    property int selectedIndex: 0
    property var segments: ["SIMULATION", "LIVE"]
    property bool interactive: true

    signal selected(int index)

    implicitWidth: 240
    implicitHeight: 38
    radius: 8
    color: "#0E1218"
    border.width: 1
    border.color: "#2A313B"
    clip: true

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Repeater {
            model: root.segments

            Rectangle {
                id: segment

                required property int index
                required property var modelData

                Layout.fillWidth: true
                Layout.fillHeight: true
                color: index === root.selectedIndex ? "#1A2029" : "#0E1218"
                border.width: index === root.selectedIndex ? 1 : 0
                border.color: "#22D3EE"

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    height: 1
                    radius: 1
                    color: "#22D3EE"
                    opacity: index === root.selectedIndex ? 0.55 : 0.08
                }

                Text {
                    anchors.centerIn: parent
                    text: segment.modelData
                    color: segment.index === root.selectedIndex ? "#E8EAED" : "#9AA3AF"
                    font.pixelSize: 12
                    font.bold: true
                    elide: Text.ElideRight
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: root.interactive
                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: {
                        root.selectedIndex = segment.index
                        root.selected(segment.index)
                    }
                }
            }
        }
    }
}
