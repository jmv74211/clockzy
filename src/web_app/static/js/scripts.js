$(document).ready(function(){
    var WEB_SERVER_URL = 'http://localhost:7000'

    // -----------------------------------------------------------------------------------------------------------------

    function send_request(endpoint, json_data, type='POST', async=false, url=WEB_SERVER_URL){
        var request = new XMLHttpRequest();
        request.open(type, url + '/' + endpoint, async);
        request.setRequestHeader('Content-Type', 'application/json');
        request.send(json_data);

        return request
    }

    // -----------------------------------------------------------------------------------------------------------------

    function create_error_alert(alert_element_id, element_id, message){
        var alert_selector_id = '#' + alert_element_id
        var element_id_selector = '#' + element_id

        // Remove alert div if exists
        if ($(alert_selector_id).length > 0){
            $(alert_selector_id).remove()
        }

        // Add alert div to the element_id
        $(element_id_selector).append('\
            <div class="alert alert-danger mt-2" id="' + alert_element_id + '"> \
                <strong>Error:</strong> ' + message + '\
            </div>');
    }
    // -----------------------------------------------------------------------------------------------------------------

    function redirect_to_index(){
        window.location.href= WEB_SERVER_URL + '/index';
    }

    // -----------------------------------------------------------------------------------------------------------------

    function get_user_id(){
        return $('#user_id').text().trim()
    }

    // -----------------------------------------------------------------------------------------------------------------

    function get_clock_data(attr_data){
        data = attr_data.replace(/["']/g, "").replace("[", "").replace("]", "")
        var array_data = data.split(', ')

        var json_data = {
            "clock_id": array_data[0],
            "date_time": array_data[1],
            "action": array_data[2]
        }

        return json_data
    }
    // -----------------------------------------------------------------------------------------------------------------

    $(document).on('click', '.button_open_modal_edit_clocking',function(){
        var clock_data = get_clock_data($(this).attr('data'))
        var action = clock_data['action']

        // // Set the values
        $('#clocking_id_edit_clocking').attr('value', clock_data['clock_id']);
        $('#input_datetime_edit_clocking').empty().append('\
             <input type="text" name="date_time" id="datetime_edit_clocking" placeholder="date_time"' +
                    'value="' + clock_data['date_time']  + '"/>'
        )

        // Remove selected values from action select
        $('#action_edit_clocking').find('option').attr('selected', false) ;

        // The following option does not work: Tried to set selected attribute dinamically.
        // The HTML code is updated correctly, but sometines is not well rendered.
        //$("#action_edit_clocking option[value=" + clock_data['action'] + "]").attr('selected', true);

        // Workaround: Delete the option item and add a new one with selected attribute.
        $('#option_' + clock_data['action']).remove()
        $('#action_edit_clocking').append(' \
            <option id="option_'+ action + '" value="' + action + '" selected="selected">' + action + '</option>'
        )
    });

    // -----------------------------------------------------------------------------------------------------------------

    $(document).on('click', '.button_open_modal_delete_clocking',function(){
        var clock_data = get_clock_data($(this).attr('data'))

        // Set the values
        $("#button_delete_clocking_yes").attr('data', clock_data['clock_id']);
    });

    // -----------------------------------------------------------------------------------------------------------------

    $("#button_update_clocking").click(function () {
        var user_id = get_user_id()
        var id= $('#clocking_id_edit_clocking').val()
        var date_time = $('#datetime_edit_clocking').val()
        var action = $('#action_edit_clocking').val()

        var data = JSON.stringify({
            "user_id": user_id,
            "clock_id": id,
            "date_time": date_time,
            "action": action
        })
        var update_request = send_request('clocking_data', data, 'PUT')

        if(update_request.status === 200){
            redirect_to_index();
        } else if(update_request.status == 400){
            create_error_alert('edit_clocking_alert_error', 'update_clocking_modal_body', update_request.responseText);
        } else {
            create_error_alert('edit_clocking_alert_error', 'update_clocking_modal_body', update_request.status);
        }
    });

    // -----------------------------------------------------------------------------------------------------------------

    $('#button_add_clocking').click(function () {
        var user_id = get_user_id()
        var date_time = $('#datetime_add_clocking').val()
        var action = $('action_add_clocking').val()

        var data = JSON.stringify({
            "user_id": user_id,
            "date_time": date_time,
            "action": action
        })
        var add_request = send_request('clocking_data', data, 'POST')

        if(add_request.status === 200){
            redirect_to_index();
        } else if(add_request.status == 400){
            create_error_alert('add_clocking_alert_error', 'add_clocking_modal_body', add_request.responseText);
        } else {
            create_error_alert('add_clocking_alert_error', 'add_clocking_modal_body', add_request.status);
        }
    });

    // -----------------------------------------------------------------------------------------------------------------

    $('#button_delete_clocking_yes').click(function () {
        var user_id = get_user_id()
        var clock_id = $(this).attr('data')

        var data = JSON.stringify({
            "user_id": user_id,
            "clock_id": clock_id
        })

        var delete_request = send_request('clocking_data', data, 'DELETE')

        if(delete_request.status === 200){
            redirect_to_index();
        } else if(delete_request.status == 400){
            create_error_alert('delete_clocking_alert_error', 'delete_clocking_modal_body',
                               delete_request.responseText);
        } else {
            create_error_alert('delete_clocking_alert_error', 'delete_clocking_modal_body', delete_request.status);
        }
    });

    // -----------------------------------------------------------------------------------------------------------------

    $('#modal_edit_data').on('hidden.bs.modal', function () {
        if ($('#edit_clocking_alert_error').length > 0){
            $('#edit_clocking_alert_error').remove()
        }
    });

    // -----------------------------------------------------------------------------------------------------------------

    $('#modal_add_clocking_data').on('hidden.bs.modal', function () {
        if ($('#add_clocking_alert_error').length > 0){
            $('#add_clocking_alert_error').remove()
        }
    });

// -----------------------------------------------------------------------------------------------------------------

    $('#modal_delete_clocking_data').on('hidden.bs.modal', function () {
        if ($('#delete_clocking_alert_error').length > 0){
            $('#delete_clocking_alert_error').remove()
        }
    });

    // -----------------------------------------------------------------------------------------------------------------

    $('#search_input').keyup(function() {
        var search = $('#search_input').val()
        var data = JSON.stringify({
            "search": search
        })

        var request = send_request('/get_query_data', data, 'POST' ,true)

        request.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                var json_response = JSON.parse(request.responseText)
                $('#table_test').html(json_response['data'])
           }
        }
    });
});
