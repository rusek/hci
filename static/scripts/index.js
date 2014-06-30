var VIEWPORT_WIDTH = 1920, VIEWPORT_HEIGHT = 1080;

function resize() {
    var winWidth = $(window).width(), winHeight = $(window).height();
    var scale = Math.max(winWidth / VIEWPORT_WIDTH, winHeight / VIEWPORT_HEIGHT);
    var offsetX = (winWidth - scale * VIEWPORT_WIDTH) / 2, offsetY = (winHeight - scale * VIEWPORT_HEIGHT) / 2;
    var transform = "scale(" + scale + ") translate(" + Math.round(offsetX) + "px, " + Math.round(offsetY) + "px)";
    $(".viewport").css("transform", transform);
}

function delayedResize() {
    if (delayedResize.timeout) {
        clearTimeout(delayedResize.timeout);
    }
    delayedResize.timeout = setTimeout(function() {
        delete delayedResize.timeout;
        resize();
    }, 100);
}

function initResize() {
    $(window).on("resize", delayedResize);
    resize();
}

function createTitlePanel(title, note) {
    return $("<div class='title-panel'></div>").append(
        $("<p class='title'></p>").append(title).append($("<span class='dot'>.</span>"))
    ).append(
        $("<p class='note'></p>").append(note)
    );
}

function createErrorPanel(note) {
    return createTitlePanel("No to klops", note);
}

function setPanel(panel, delay) {
    if (setPanel.timeout) {
        clearTimeout(setPanel.timeout);
        delete setPanel.timeout;
    }

    if (delay) {
        setPanel.timeout = setTimeout(function() {
            delete setPanel.timeout;
            $(".viewport").empty().append(panel);
        }, delay);
    } else {
        $(".viewport").empty().append(panel);
    }
}

function sameDay(date1, date2) {
    return date1.getDay() === date2.getDay() && date1.getMonth() === date2.getMonth() &&
        date1.getFullYear() === date2.getFullYear();
}

function addDays(date, days) {
    return new Date(date.getTime() + days * (24 * 60 * 60 * 1000));
}

function getDayMinutes(date) {
    return date.getHours() * 60 + date.getMinutes();
}

function filterActivitiesByDate(activities, date) {
    return activities.filter(function(activity) {
        return sameDay(activity.start_time, date);
    });
}

function zeroPad(string, length) {
    string = String(string);
    if (length > string.length) {
        string = new Array(length - string.length + 1).join("0") + string;
    }
    return string;
}

function createTTPanel(start, activities) {
    var node = $("<div class='time-table'></div>");

    start = new Date(start);
    activities.forEach(function(activity) {
        activity.start_time = new Date(activity.start_time.replace(" ", "T"));
        activity.end_time = new Date(activity.end_time.replace(" ", "T"));
    });

    var minY = 100, maxY = VIEWPORT_HEIGHT - 50;
    var minHour = 8, maxHour = 18;
    var minX = 120, maxX = VIEWPORT_WIDTH - 120;
    var colSep = 50;
    var numCols = 3;
    var colWidth = Math.round((maxX - minX - (numCols - 1) * colSep) / numCols);
    maxX = minX + numCols * (colWidth + colSep) - colSep; // due to rounding errors

    function findMinMaxHour() {
        activities.forEach(function(activity) {
            minHour = Math.min(minHour, activity.start_time.getHours());
            maxHour = Math.max(maxHour, activity.end_time.getHours() + (activity.end_time.getMinutes() ? 1 : 0));
        });
    }

    findMinMaxHour();

    function dateToY(date) {
        return Math.round((getDayMinutes(date) / 60 - minHour) / (maxHour - minHour) * (maxY - minY) + minY);
    }

    for (var i = minHour; i <= maxHour; i++) {
        var y = dateToY(new Date(1970, 1, 1, i));
        var labelHeight = 40;
        node.append(
            $("<div class='hour'></div>").css({
                position: "absolute",
                top: (y - labelHeight / 2) + "px",
                width: "100px",
                "line-height": labelHeight + "px",
                left: "10px"
            }).text(i + ":00")
        );
        node.append(
            $("<div class='hour'></div>").css({
                position: "absolute",
                top: (y - labelHeight / 2) + "px",
                "line-height": labelHeight + "px",
                left: maxX + "px",
                width: "70px"
            }).text(i + ":00")
        );

        var lineWidth = 4;
        node.append(
            $("<div class='horizontal-line'></div>").css({
                position: "absolute",
                top: (y - lineWidth / 2) + "px",
                height: lineWidth + "px",
                left: minX + "px",
                width: (maxX - minX) + "px"
            })
        );
    }

    function renderActivities(dayShift) {
        var date = addDays(start, dayShift);
        var dateString = zeroPad(date.getDate(), 2) + "-" + zeroPad(date.getMonth() + 1, 2) + "-" + date.getFullYear();

        node.append(
            $("<div class='day'></div>").css({
                position: "absolute",
                top: 0,
                "height": minY + "px",
                width: colWidth + "px",
                left: (minX + dayShift * (colWidth + colSep)) + "px",
                "font-size": "30px"
            }).append(
                "<p class='name'>" + ["Dzisiaj", "Jutro", "Pojutrze"][dayShift] + "<span class='dot'>.</span></p>" +
                    "<p class='numeric'>" + dateString + "</p>"
            )
        );

        filterActivitiesByDate(activities, date).forEach(function (activity) {
            var top = dateToY(activity.start_time), bottom = dateToY(activity.end_time);

            var activityNode = $("<div class='activity'></div>").css({
                position: "absolute",
                left: (minX + dayShift * (colWidth + colSep)) + "px",
                top: top + "px",
                height: (bottom - top) + "px",
                width: colWidth + "px"
            }).append(
                $("<p class='name'></p>").text(activity.name.pl)
            );

            if (activity.room_number) {
                activityNode.append(
                    $("<p class='room'></p>").append("Sala " + activity.room_number +
                        ", <span class='building-name'>" + activity.building_name.pl + "</span>")
                );
            }

            node.append(activityNode);
        });
    }

    renderActivities(0);
    renderActivities(1);
    renderActivities(2);

    return node;
}


function createCrstestsPanel(tests) {
    var node = $("<div class='course-tests'></div>");

    var minX = 50, maxX = VIEWPORT_WIDTH - 50;
    var colSep = 50;
    var numCols = 3;
    var colWidth = Math.round((maxX - minX - (numCols - 1) * colSep) / numCols);
    maxX = minX + numCols * (colWidth + colSep) - colSep; // due to rounding errors

    function renderTest(test) {
        function renderNode(node) {
            var li = $("<li></li>");
            var label = $("<p class='node-label'></p>");
            label.append($("<span class='node-name'></span>").text(node.name.pl));
            function setSentinelValue(text) {
                label.append($("<span class='node-value sentinel'></span>").text(text));
            }

            if (node.type === "task") {
                if (!node.visible_for_students) {
                    setSentinelValue('(punkty ukryte)');
                } else if (!node.user_points || typeof node.user_points.points !== "number") {
                    setSentinelValue('(brak punktów)');
                } else {
                    label.append(
                        $("<span class='node-value'></span>").text(
                            String(node.user_points.points).replace(/\./, ",")
                        ).append(
                            "&nbsp;"
                        ).append(
                            $("<span class='node-unit'>pkt</span>")
                        )
                    );
                }
            }

            if (node.type === "grade") {
                if (!node.visible_for_students) {
                    setSentinelValue('(ocena ukryta)');
                } else if (!node.user_grade || !node.user_grade.grade) {
                    setSentinelValue('(brak oceny)');
                } else {
                    label.append(
                        $("<span class='node-value'></span>").text(
                            node.user_grade.grade.symbol
                        ).append(
                            "&nbsp;"
                        ).append(
                            $("<span class='node-unit' style='visibility: hidden'>pkt</span>")
                        )
                    );
                }
            }

            li.append(label);
            if (node.subnodes.length) {
                var ul = $("<ul></ul>");
                node.subnodes.forEach(function(subnode) {
                    ul.append(renderNode(subnode));
                });
                li.append(ul);
            }
            return li;
        }

        var testNode = $("<div class='test'></div>");
        testNode.append(
            $("<p></p>").text(
                test.course_edition.course_name.pl
            ).append(
                $("<span class='dot'>.</span>")
            )
        );
        var ulNode = $("<ul></ul>");
        test.subnodes.forEach(function(subnode) {
            ulNode.append(renderNode(subnode));
        });
        testNode.append(ulNode);
        return testNode;
    }

    /*function countUsedColumns(testNode) {
        var markerNode = $("<li></li>").css({
        });
        markerNode.appendTo(testNode.children("ul"));
        testNode.appendTo("body");

        console.log(markerNode.position());

        //markerNode.detach();
        testNode.detach();
    }*/

    tests.forEach(function(test, i) {
        if (i >= numCols) {
            return;
        }
        var testNode = renderTest(test);
        testNode.css({
            position: "absolute",
            width: colWidth + "px",
            height: VIEWPORT_HEIGHT + "px",
            top: "0",
            left: (minX + i * (colWidth + colSep)) + "px"
        });

        node.append(testNode);
    });

    return node;
}

function createPanelFromData(data) {
    switch (data.type) {
    case "greeting":
        //return createTitlePanel("Witaj", "Pokaż mi swoją legitymację, a powiem Ci, kim <em>jesteś</em>.");
        return createTitlePanel("Witaj", "Przyłóż <em>legitymację studencką</em> do czytnika kart.");

    case "tt":
        return createTTPanel(data.start, data.activities);

    case "crstests":
        return createCrstestsPanel(data.tests);

    case "loading":
        return createTitlePanel("Czekaj", "Pobieram dane.");

    case "bad_card":
        return createErrorPanel("Nie udało się rozpoznać karty.");

    default:
        return createTitlePanel("Odebrano komunikat", data.text);
    }
}

window.onload = function() {
    setTimeout(function() {
        var eventSource = new EventSource("/panel-feed");
        eventSource.onmessage = function(event) {
            console.log("Received panel", event.data);
            var data = JSON.parse(event.data);
            if (data) {
                setPanel(
                    createPanelFromData(data),
                    data.type === "loading" ? 300 : 0
                );
            }
        };
        eventSource.onerror = function() {
            setPanel(createErrorPanel("Utracono połączenie z serwerem."));
            setTimeout(function() {
                window.location = window.location;
            }, 5000);
        }
    }, 200);

    initResize();
};

