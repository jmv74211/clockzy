$(document).ready(function(){

    function send_request(endpoint, json_data, type="POST", url="http://localhost:7000"){
        var request = new XMLHttpRequest();
        request.open(type, url + "/" + endpoint, false);
        request.setRequestHeader('Content-Type', 'application/json');
        request.send(json_data);

        return request
    }

    $(".edit_clocking").click(function () {
        var data = $(this).attr("data")

        // Clean string
        data = data.replace(/["']/g, "").replace("[", "").replace("]", "")

        //Set the array and variables
        var array_data = data.split(", ")
        var clock_id = array_data[0]
        var clock_datetime = array_data[1]
        var clock_action = array_data[2]

        // Set the values
        $("#datetime_edit_clocking").attr('value', clock_datetime);
        $("#action_edit_clocking").attr('value', clock_action);
        $("#id_edit_clocking").attr('value', clock_id);

        //$("#action_select option:selected").removeAttr('selected');
        //$("#action_select option[value="+ clock_action +"]").attr('selected', '');

    });



    $("#button_update_clocking").click(function () {
        // console.log($("#datetime_edit_clocking").attr('value'));
        // console.log($("#action_edit_clocking").attr('value'));
        var id= $("#id_edit_clocking").val()
        var date_time = $("#datetime_edit_clocking").val()
        var action = $("#action_edit_clocking").val()

        // const regex = new RegExp("\d\d\d\d-\d\d-\d\d\s\d\d:\d\d:\d\d")
        // console.log(validate_date_time(date_time))
        // var y = date_time.match(/\d\d\d\d-\d\d-\d\d\s\d\d:\d\d:\d\d/) //regex.test(date_time)
        //console.log(y)
        // $("#clocking_edit_validation").css("display", "block")
        var data = JSON.stringify({
            "id": id,
            "date_time": date_time,
            "action": action
        })
        var update_request = send_request("update_clocking_data", data)

        if(update_request.status === 200){
            window.location.href="http://localhost:7000/index";
        }
    });

    $("#button_add_clocking").click(function () {
        var user_id = $("#user_id").text().trim()
        var date_time = $("#datetime_add_clocking").val()
        var action = $("#action_add_clocking").val()

        var data = JSON.stringify({
            "user_id": user_id,
            "date_time": date_time,
            "action": action
        })
        var update_request = send_request("add_clocking_data", data)

        if(update_request.status === 200){
            window.location.href="http://localhost:7000/index";
        }
    });

    $('#modal_edit_data').on('hidden.bs.modal', function () {
        $("#clocking_edit_validation").css("display", "none")
    });


    $(".delete_clocking").click(function () {
        var data = $(this).attr("data")

        // Clean string
        data = data.replace(/["']/g, "").replace("[", "").replace("]", "")

        //Set the array and variables
        var array_data = data.split(", ")
        var clock_id = array_data[0]
        // Set the values
        $("#button_delete_clocking_yes").attr('clock_id', clock_id);
    });



    $("#button_delete_clocking_yes").click(function () {
        var data = $(this).attr("clock_id")

        // Clean string
        data = data.replace(/["']/g, "").replace("[", "").replace("]", "")

        //Set the array and variables
        var array_data = data.split(", ")
        var clock_id = array_data[0]
        var user_id = $("#user_id").text().trim()

        var data = JSON.stringify({
            "user_id": user_id,
            "clock_id": clock_id
        })
        console.log(data)
        var delete_request = send_request("delete_clocking_data", data)

        if(delete_request.status === 200){
            window.location.href="http://localhost:7000/index";
        }
    });


});