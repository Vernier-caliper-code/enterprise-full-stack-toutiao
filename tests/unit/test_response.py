from toutiao_backend.utils.response import ApiResponse, success_response


def test_success_response_uses_default_envelope() -> None:
    # Arrange
    payload = {"id": 7, "title": "unit test"}

    # Act
    response = success_response(data=payload)

    # Assert
    assert response.code == 200
    assert response.message == "success"
    assert response.data == payload
    assert response.model_dump() == {
        "code": 200,
        "message": "success",
        "data": payload,
    }


def test_success_response_preserves_custom_message_and_null_data() -> None:
    # Arrange
    message = "operation completed"

    # Act
    response = success_response(message=message)

    # Assert
    assert isinstance(response, ApiResponse)
    assert response.message == message
    assert response.data is None
