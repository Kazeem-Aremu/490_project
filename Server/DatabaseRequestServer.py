from flask import Flask, request, jsonify
from flask_cors import CORS
from DataBaseHandler import DataBaseHandler

# ------------------------------------------------------------
# App setup
# ------------------------------------------------------------
app = Flask(__name__)

# Allow React dev server to call this API
CORS(app)

# Single global database handler instance
Handler = DataBaseHandler()
testStudent = {
    "id":"4321", 
    "NAME":"Jane Doe", 
    "ROLE": "Student"
    }

@app.route("/")
def home():
    return "Server Up and running!"


# ------------------------------------------------------------
# USER ROUTES
# ------------------------------------------------------------

@app.route("/getUser", methods=["GET"])
def getUserData():
    try:
        user_Id_Raw = request.args.get("useriD")
        if not user_Id_Raw:
            return jsonify({"error": "User_ID query parameter is required"}), 400
        try:
            userID = int(user_Id_Raw)
        except ValueError:
            return jsonify({"error": "User Id must be an integer"}), 400
        info = Handler.getUser(userID)
        return jsonify(info), 200
    except Exception as e:
        print("ERROR in /getUser:", e)
        return jsonify({"error": "something went wrong", "detail": str(e)}), 500


@app.route("/createUser", methods=["POST"])
def createPatient():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        #result = Handler.createUser(data)
        result = Handler.createUser(testStudent)
        status = 201 if not isinstance(result, dict) or "error" not in result else 500
        return jsonify(result), status
    except Exception as e:
        print("ERROR in /createUser:", e)
        return jsonify({"error": "something went wrong", "detail": str(e)}), 500


# # # ------------------------------------------------------------
# # # DOCTOR ROUTES
# # # ------------------------------------------------------------

# # @app.route("/getDoctor", methods=["GET"])
# # def getDoctorData():
# #     """
# #     GET /getDoctor?Doctor_ID=1
# #     Returns doctor data for the given Doctor_ID using Handler.getDoctor
# #     """
# #     try:
        
# #         doctor_id_raw = request.args.get("Doctor_ID")
# #         if not doctor_id_raw:
# #             return jsonify({"error": "Doctor_ID query parameter is required"}), 400

# #         try:
# #             doctor_id = int(doctor_id_raw)
           
# #         except ValueError:
# #             return jsonify({"error": "Doctor_ID must be an integer"}), 400

# #         info = Handler.getDoctor(doctor_id)
# #         return jsonify(info), 200
# #     except Exception as e:
# #         print("ERROR in /getDoctor:", e)
# #         return jsonify({"error": "something went wrong", "detail": str(e)}), 500


# @app.route("/getAppointmentDR", methods=["GET"])
# def getDoctorAppointment():
#     """
#     GET /getAppointmentDR?Doctor_ID=1
#     Returns list of appointments for the given doctor using Handler.doctorGetAppointment
#     """
#     try:
        

#         doctor_id_raw = request.args.get("Doctor_ID")
#         if not doctor_id_raw:
#             return jsonify({"error": "Doctor_ID query parameter is required"}), 400

#         try:
#             doctor_id = int(doctor_id_raw)
          
#         except ValueError:
#             return jsonify({"error": "Doctor_ID must be an integer"}), 400

#         info = Handler.doctorGetAppointment(doctor_id)
#         return jsonify(info), 200
#     except Exception as e:
#         print("ERROR in /getAppointmentDR:", e)
#         return jsonify({"error": "something went wrong", "detail": str(e)}), 500


# @app.route("/createDoctor", methods=["POST"])
# def createDoctor():
#     """
#     POST /createDoctor
#     JSON body should match what Handler.createDoctor expects.
#     """
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "JSON body required"}), 400

#         result = Handler.createDoctor(data)
#         status = 201 if not isinstance(result, dict) or "error" not in result else 500
#         return jsonify(result), status
#     except Exception as e:
#         print("ERROR in /createDoctor:", e)
#         return jsonify({"error": "something went wrong", "detail": str(e)}), 500


# # ------------------------------------------------------------
# # APPOINTMENT CREATION
# # ------------------------------------------------------------

# @app.route("/createAppointment", methods=["POST"])
# def createAppointment():
#     """
#     POST /createAppointment
#     JSON body should match what Handler.createAppointment expects.
#     """
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "JSON body required"}), 400

#         result = Handler.createAppointment(data)
#         status = 201 if not isinstance(result, dict) or "error" not in result else 500
#         return jsonify(result), status
#     except Exception as e:
#         print("ERROR in /createAppointment:", e)
#         return jsonify({"error": "something went wrong", "detail": str(e)}), 500


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
