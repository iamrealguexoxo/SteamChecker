import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    id: root
    width: 1000
    height: 700
    visible: true
    title: "Steam Workshop Checker (QML)"

    // App state updated via controller signals
    property int progCurrent: 0
    property int progTotal: 100
    property bool running: false
    property string statusText: "Bereit."
    property string summaryText: ""
    property string cleanedList: ""
    property string theme: "dark"
    property bool filtersExpanded: false
    // Filter state
    property string statusFilter: "ALLE"      // ALLE | OK | GELÖSCHT | NO_TITLE | FEHLER
    property string warningFilter: "ALLE"     // ALLE | MIT | OHNE
    property string compareFilter: "ALLE"     // ALLE | OK | Gemischt | Zusätzlich

    function rowVisible(rowStatus, rowWarning, rowCompare) {
        // Status filter
        if (statusFilter !== "ALLE") {
            if (statusFilter === "FEHLER") {
                if (rowStatus === "OK" || rowStatus === "GELÖSCHT" || rowStatus === "NO_TITLE") return false;
            } else if (rowStatus !== statusFilter) return false;
        }
        // Warning filter
        if (warningFilter !== "ALLE") {
            const hasWarn = !!rowWarning && rowWarning.length > 0;
            if (warningFilter === "MIT" && !hasWarn) return false;
            if (warningFilter === "OHNE" && hasWarn) return false;
        }
        // Compare filter
        if (compareFilter !== "ALLE") {
            if (compareFilter === "Gemischt" && rowCompare !== "mixed") return false;
            else if (compareFilter === "Zusätzlich" && rowCompare !== "extra") return false;
            else if (compareFilter === "OK" && rowCompare !== "match") return false;
        }
        return true;
    }

    // Theme toggle
    Material.theme: theme === "dark" ? Material.Dark : Material.Light
    Material.accent: Material.Teal
    Material.primary: Material.Indigo

    // Listen to controller updates
    Connections {
        target: controller
        function onProgressChanged(current, total) {
            root.progCurrent = current
            root.progTotal = Math.max(1, total)
        }
        function onStatusChanged(text) { root.statusText = text }
        function onSummaryChanged(text) { root.summaryText = text }
        function onCleanedListChanged(text) { root.cleanedList = text }
        function onRunningChanged(isRunning) { root.running = isRunning }
        function onFinished() { /* no-op */ }
        function onComparisonReady(txt) {
            compareDialog.text = txt
            compareDialog.open()
        }
    }

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            spacing: 8
            ToolButton {
                text: "Prüfen"
                enabled: !root.running
                onClicked: controller.startCheck(idsInput.text)
            }
            ToolButton {
                text: "Warnungs-Mods entfernen"
                enabled: !root.running
                onClicked: controller.removeWarnings()
            }
            ToolButton {
                text: "Mod-IDs vergleichen"
                enabled: !root.running
                onClicked: comparePrompt.open()
            }
            ToolButton {
                text: "ℹ Über"
                onClicked: aboutDialog.open()
            }
            Item { Layout.fillWidth: true }
            ToolButton {
                text: "Abbrechen"
                enabled: root.running
                onClicked: controller.cancel()
            }
            ToolButton {
                text: theme === "dark" ? "☀️" : "🌙"
                onClicked: theme = theme === "dark" ? "light" : "dark"
                ToolTip.visible: hovered
                ToolTip.text: "Theme wechseln (Hell/Dunkel)"
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // IDs input
        Label { text: "Workshop-IDs (mit ';' trennen):" }
        TextArea {
            id: idsInput
            placeholderText: "2709866494;3445949422;3445362877"
            Layout.fillWidth: true
            Layout.preferredHeight: 70
            wrapMode: TextEdit.NoWrap
            selectByMouse: true
            readOnly: root.running
        }

        // Progress and status
        ProgressBar {
            Layout.fillWidth: true
            from: 0
            to: Math.max(1, root.progTotal)
            value: root.progCurrent
        }
        Label {
            text: root.statusText
            elide: Label.ElideRight
        }

        // Filter controls (collapsible)
        Frame {
            Layout.fillWidth: true
            padding: 6
            ColumnLayout {
                anchors.fill: parent
                spacing: 6
                // Header with toggle
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Label { text: "Filter"; font.bold: true }
                    ToolButton {
                        text: root.filtersExpanded ? "▾" : "▸"
                        onClicked: root.filtersExpanded = !root.filtersExpanded
                        ToolTip.visible: hovered
                        ToolTip.text: root.filtersExpanded ? "Filter einklappen" : "Filter ausklappen"
                    }
                    Item { Layout.fillWidth: true }
                    Label { text: "(Filter live)"; opacity: 0.55; font.pixelSize: 11 }
                }
                // Content
                RowLayout {
                    id: filterRow
                    visible: root.filtersExpanded
                    height: visible ? implicitHeight : 0
                    spacing: 10
                    opacity: visible ? 1 : 0
                    Behavior on height { NumberAnimation { duration: 120 } }
                    Behavior on opacity { NumberAnimation { duration: 120 } }
                    ComboBox {
                        id: statusBox
                        model: ["ALLE","OK","GELÖSCHT","NO_TITLE","FEHLER"]
                        currentIndex: 0
                        onCurrentTextChanged: statusFilter = currentText
                        Layout.preferredWidth: 95
                        font.pixelSize: 12
                        height: 26
                    }
                    ComboBox {
                        id: warningBox
                        model: ["ALLE","MIT","OHNE"]
                        currentIndex: 0
                        onCurrentTextChanged: warningFilter = currentText
                        Layout.preferredWidth: 80
                        font.pixelSize: 12
                        height: 26
                    }
                    ComboBox {
                        id: compareBox
                        model: ["ALLE","OK","Gemischt","Zusätzlich"]
                        currentIndex: 0
                        onCurrentTextChanged: compareFilter = currentText
                        Layout.preferredWidth: 95
                        font.pixelSize: 12
                        height: 26
                    }
                    Item { Layout.fillWidth: true }
                }
            }
        }

        // Results list acting like a table
        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 6
                // Header row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Label { text: "Workshop-ID"; font.bold: true; Layout.preferredWidth: 150 }
                    Label { text: "Status"; font.bold: true; Layout.preferredWidth: 110 }
                    Label { text: "Titel + Mod-ID(s)"; font.bold: true; Layout.fillWidth: true }
                    Label { text: "Vergleich"; font.bold: true; Layout.preferredWidth: 120 }
                    Label { text: "Warnung"; font.bold: true; Layout.preferredWidth: 160 }
                }
                Rectangle { height: 1; color: Material.theme === Material.Dark ? "#333" : "#ccc"; Layout.fillWidth: true }
                ListView {
                    id: listView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: resultModel
                    clip: true
                    onCountChanged: if (root.running) listView.positionViewAtEnd()
                    delegate: Item {
                        width: listView.width
                        height: visible ? 30 : 0
                        visible: root.rowVisible(status, warning, compareTag)
                        Rectangle { // subtle alternating row background for dark theme readability
                            anchors.fill: parent
                            color: theme === "dark" ? (index % 2 ? "#24262d" : "#1f2126") : "transparent"
                            z: -1
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 2
                            spacing: 10
                            Item {
                                Layout.preferredWidth: 150
                                Layout.fillHeight: true
                                Label {
                                    id: widLabel
                                    anchors.fill: parent
                                    anchors.rightMargin: 6
                                    text: wid
                                    color: fgColor
                                    font.pixelSize: 13
                                    elide: Label.ElideRight
                                    font.underline: widMouse.containsMouse
                                    ToolTip.visible: widMouse.containsMouse
                                    ToolTip.text: "Im Browser öffnen"
                                }
                                MouseArea {
                                    id: widMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: Qt.openUrlExternally('https://steamcommunity.com/sharedfiles/filedetails/?id=' + wid)
                                }
                            }
                            Label { text: status; color: fgColor; font.pixelSize: 13; Layout.preferredWidth: 110; elide: Label.ElideRight }
                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Label {
                                    id: titleLabel
                                    anchors.fill: parent
                                    anchors.rightMargin: 6
                                    text: title
                                    color: fgColor
                                    font.pixelSize: 13
                                    elide: Label.ElideRight
                                    font.underline: titleArea.containsMouse
                                    ToolTip.visible: titleArea.containsMouse
                                    ToolTip.text: "Im Browser öffnen"
                                }
                                MouseArea {
                                    id: titleArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: Qt.openUrlExternally('https://steamcommunity.com/sharedfiles/filedetails/?id=' + wid)
                                }
                            }
                            // Compare tag pill
                            Item {
                                Layout.preferredWidth: 120
                                Layout.fillHeight: true
                                Rectangle {
                                    id: cmpPill
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: cmpText.implicitWidth + 16
                                    height: 20
                                    radius: 10
                                    visible: compareTag && compareTag !== "none"
                                    color: compareTag === "extra" ? "#64b5f6" : (compareTag === "mixed" ? "#ffa726" : "#66bb6a")
                                    Text {
                                        id: cmpText
                                        anchors.centerIn: parent
                                        color: theme === "dark" ? "#0f0f0f" : "#111"
                                        font.pixelSize: 12
                                        text: compareTag === "extra" ? "Zusätzlich" : (compareTag === "mixed" ? "Gemischt" : "OK")
                                    }
                                }
                            }
                            Label { text: warning; color: fgColor; font.pixelSize: 13; Layout.preferredWidth: 160; elide: Label.ElideRight }
                        }

                        // Context menu for quick copy actions
                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.RightButton
                            onPressed: function(mouse){
                                if (mouse.button === Qt.RightButton) {
                                    ctxMenu.popup()
                                }
                            }
                            Menu {
                                id: ctxMenu
                                MenuItem {
                                    text: "Link kopieren"
                                    onTriggered: Qt.application.clipboard.setText('https://steamcommunity.com/sharedfiles/filedetails/?id=' + wid)
                                }
                                MenuItem {
                                    text: "ID kopieren"
                                    onTriggered: Qt.application.clipboard.setText(String(wid))
                                }
                            }
                        }
                    }
                }
            }
        }

        // Summary
        Label { text: root.summaryText }

        // Cleaned list + copy
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Label { text: "Bereinigte Liste:" }
            TextField {
                Layout.fillWidth: true
                text: root.cleanedList
                readOnly: true
                selectByMouse: true
            }
            Button {
                text: "In Zwischenablage kopieren"
                onClicked: controller.copyCleaned()
            }
        }
    }

    // Compare prompt dialog
    Dialog {
        id: comparePrompt
        title: "Mod-IDs vergleichen"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose
        width: 640
        contentItem: ColumnLayout {
            anchors.margins: 12
            spacing: 8
            TextField {
                id: compareInput
                placeholderText: "iMeds;SomeOther;Another"
                Layout.preferredWidth: 520
            }
        }
        onAccepted: controller.compareModIds(compareInput.text)
    }

    // Compare results dialog
    Dialog {
        id: compareDialog
        title: "Vergleich"
        modal: true
        standardButtons: Dialog.Ok
        width: 640
        property string text: ""
        contentItem: ScrollView {
            implicitWidth: 560
            implicitHeight: 420
            TextArea {
                width: parent.width
                text: compareDialog.text
                wrapMode: TextEdit.Wrap
                readOnly: true
                selectByMouse: true
                background: null
            }
        }
    }

    // About dialog with animated GIF
    Dialog {
        id: aboutDialog
        title: "Über dieses Tool"
        modal: true
        standardButtons: Dialog.Ok
        width: 420
        contentItem: ColumnLayout {
            anchors.margins: 12
            spacing: 10
            Loader {
                width: 320; height: 220
                active: hasBartGif
                sourceComponent: AnimatedImage {
                    source: bartGifUrl
                    fillMode: Image.PreserveAspectFit
                    width: 320
                    height: 220
                    playing: true
                }
            }
            Label { visible: !hasBartGif; text: "Bart GIF nicht gefunden. Lege 'python_steam_checker/assets/bart.gif' ab." }
            Label { text: "made with ♥ by iamguexoxo" }
        }
    }
}
