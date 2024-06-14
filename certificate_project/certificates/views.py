from django.shortcuts import render
from django.http import HttpResponse, FileResponse

from django.shortcuts import render, redirect
from .models import *
from django.conf import settings
from django.contrib.auth.hashers import *
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import csv
import os, io
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

import blake3, requests
from web3 import Web3
import json

from datetime import datetime
from django.http import HttpResponse
import ipfshttpclient
from django.urls import reverse
from django.http import HttpResponseRedirect

import PyPDF2

from django.core.files.storage import FileSystemStorage


ganache_url = "http://127.0.0.1:7545"  # Use the correct Ganache URL
web3 = Web3(Web3.HTTPProvider(ganache_url))
# Load contract ABI
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "certificates", "StudentDataStorage.json")) as f:
    contract_data = json.load(f)
contract_abi = contract_data["abi"]
# Contract address
contract_address = ""  # Replace with the deployed contract address
checksum_coontract_address = web3.to_checksum_address(contract_address)
# Initialize contract
contract = web3.eth.contract(address=checksum_coontract_address, abi=contract_abi)
# account = "0x0003af35903BBDb31575B8Ec7ce19179583BF7aa"


User = get_user_model()


def logout_view(request):
    logout(request)
    return redirect("student_login")


def student_register(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if student with email already exists
        existing_student = Student.objects.filter(email=email).first()

        if existing_student:
            error_message = "User with this email already exists."
            return render(
                request, "student_register.html", {"error_message": error_message}
            )
        else:
            # Hash the password only if a new student is being created
            hashed_password = make_password(password)

            # Create a new student
            new_student = Student(
                name=full_name,
                email=email,
                password=hashed_password,
                certificate_issued=False,
            )
            new_student.save()

            # Redirect to student login page after successful registration
            return redirect("student_login")
    else:
        return render(request, "student_register.html")


def student_login(request):
    if request.method == "POST":
        # Check student credentials and log them in using email
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            student = Student.objects.get(email=email)
            if check_password(password, student.password):
                # Assuming successful login, redirect to student dashboard
                return redirect("student_dashboard", student_id=student.pk)
        except Student.DoesNotExist:
            pass
        # If login fails or student doesn't exist, show error message
        error_message = "Invalid credentials. Please try again."
        return render(request, "student_login.html", {"error_message": error_message})
    else:
        return render(request, "student_login.html")


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active and user.is_staff:
            login(request, user)
            return redirect("admin_dashboard")
        else:
            error_message = "Invalid credentials. Please try again."
            return render(request, "admin_login.html", {"error_message": error_message})
    else:
        return render(request, "admin_login.html")


def admin_dashboard(request):
    print(request.user.username)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    csv_file_path = os.path.join(BASE_DIR, "certificates", "students_dataset.csv")
    students = Student.objects.all()

    if request.method == "POST":
        student_id = request.POST.get("student_id")
        student = Student.objects.get(id=student_id)

        # Check if certificate is already issued
        if not student.certificate_issued:
            # Read students_dataset.csv file
            with open(csv_file_path, mode="r") as csv_file:
                csv_reader = csv.DictReader(csv_file)

                # Find the student's record by name
                for row in csv_reader:
                    if row["student_name"] == student.name:
                        # Check marks for each semester
                        sem1_marks = [
                            int(row["sem1_sub1_mark"]),
                            int(row["sem1_sub2_mark"]),
                            int(row["sem1_sub3_mark"]),
                            int(row["sem1_sub4_mark"]),
                        ]
                        sem2_marks = [
                            int(row["sem2_sub1_mark"]),
                            int(row["sem2_sub2_mark"]),
                            int(row["sem2_sub3_mark"]),
                            int(row["sem2_sub4_mark"]),
                        ]
                        sem3_marks = [
                            int(row["sem3_sub1_mark"]),
                            int(row["sem3_sub2_mark"]),
                            int(row["sem3_sub3_mark"]),
                            int(row["sem3_sub4_mark"]),
                        ]
                        sem4_marks = [
                            int(row["sem4_sub1_mark"]),
                            int(row["sem4_sub2_mark"]),
                            int(row["sem4_sub3_mark"]),
                            int(row["sem4_sub4_mark"]),
                        ]

                        # Check if all marks in each semester are 50 or above
                        all_marks_above_50 = all(
                            mark >= 50
                            for mark in sem1_marks
                            + sem2_marks
                            + sem3_marks
                            + sem4_marks
                        )

                        # Check if club hours are 80 or above
                        club_hours = int(row["club_hours"])

                        if all_marks_above_50 and club_hours >= 80:
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            font_path = os.path.join(current_dir, "Prata-Regular.ttf")
                            op_path = os.path.join(current_dir, "output", "op.pdf")
                            t_path = os.path.join(current_dir, "TEMPLATE.pdf")
                            pdfmetrics.registerFont(TTFont("prata", font_path))
                            packet = io.BytesIO()
                            c = canvas.Canvas(packet, pagesize=letter)
                            c.setFont("prata", 35)
                            c.drawString(300, 560, "Amity University")
                            c.setFillColorRGB(146 / 255, 88 / 255, 46 / 255)
                            c.setFont("prata", 40)
                            c.drawString(300, 400, student.name)
                            c.setFillColorRGB(0, 0, 0)
                            c.setFont("prata", 12)
                            c.drawString(405, 286, "Second Class")
                            c.save()
                            packet.seek(0)
                            overlay = PdfReader(packet)
                            template = PdfReader(t_path)
                            output = PdfWriter()
                            for i in range(len(template.pages)):
                                page = template.pages[i]
                                page.merge_page(overlay.pages[0])
                                output.add_page(page)

                            with open(op_path, "wb") as outputStream:
                                output.write(outputStream)

                            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                            ipfs_hash = upload_to_pinata(
                                op_path,
                                student.name,
                                current_time,
                                request.user.username,
                            )
                            with open(op_path, "rb") as file:
                                file_contents = file.read()
                                hash_digest = blake3.blake3(file_contents).hexdigest()
                            no = upload_to_bkchain(
                                student.name,
                                request.user.username,
                                ipfs_hash,
                                hash_digest,
                                current_time,
                            )
                            student.certificate_issued = True
                            student.save()
                            break  # Once certificate is issued, exit the loop

    context = {
        "students": students,
    }

    return render(request, "admin_dashboard.html", context)


def upload_to_pinata(file_path, student_name, timestamp, admin_name):
    pinata_api_key = ""
    pinata_secret_api_key = (
        ""
    )
    JWT = ""

    headers = {
        "pinata_api_key": pinata_api_key,
        "pinata_secret_api_key": pinata_secret_api_key,
        "Authorization": f"Bearer {JWT}",
    }

    with open(file_path, "rb") as file:
        file_data = {"file": file.read()}
    response = requests.post(
        "https://api.pinata.cloud/pinning/pinFileToIPFS",
        files=file_data,
        headers=headers,
    )
    if response.status_code == 200:
        json_response = response.json()
        ipfs_hash = json_response["IpfsHash"]
        return ipfs_hash
    else:
        print("Failed to upload file to Pinata IPFS.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return None


def upload_to_bkchain(student_name, admin_name, ipfs_hash, blake3_hash, timestamp):
    tx_hash = contract.functions.addStudentData(
        student_name,
        admin_name,
        ipfs_hash,
        blake3_hash,
        timestamp,
    ).transact({"from": web3.eth.accounts[0]})
    print("Student data added successfully.")
    return None


def get_student_data_by_name(student_name):
    # Convert string to bytes
    # student_name_bytes = web3.toBytes(text=student_name)

    # Query student data by studentName
    student_data = contract.functions.getStudentDataByQuery(
        "studentName", student_name
    ).call()
    return {
        "studentName": student_data[0],
        "adminName": student_data[1],
        "ipfsHash": student_data[2],
        "blake3Hash": student_data[3],
        "timestamp": student_data[4],
    }


def get_student_data_by_ipfs(ipfs_hash):
    # Convert string to bytes
    ipfs_hash_bytes = web3.toBytes(text=ipfs_hash)

    # Query student data by ipfsHash
    student_data = contract.functions.getStudentDataByQuery(
        "ipfsHash", ipfs_hash_bytes
    ).call()
    return {
        "studentName": web3.toText(student_data[0]),
        "adminName": web3.toText(student_data[1]),
        "ipfsHash": web3.toText(student_data[2]),
        "blake3Hash": web3.toText(student_data[3]),
        "timestamp": student_data[4],
    }


def download_from_ipfs(ipfs_hash):
    pinata_base_url = "https://gateway.pinata.cloud/ipfs/"
    file_url = pinata_base_url + ipfs_hash
    print(file_url)
    return file_url


def download_certificate(request, student_name):
    std = Student.objects.get(name=student_name)
    data = get_student_data_by_name(student_name)
    x = data["ipfsHash"]
    y = download_from_ipfs(x)
    redirect_url = reverse("student_dashboard", kwargs={"student_id": std.id})
    redirect_url += f"?file_link={y}"
    return HttpResponseRedirect(redirect_url)


def student_dashboard(request, student_id):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file_path = os.path.join(BASE_DIR, "certificates", "students_dataset.csv")
    # Assuming you retrieve student data from the database
    s = Student.objects.get(pk=student_id)
    student_data = {}
    with open(csv_file_path, mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row["student_name"] == s.name:
                student_data["Name"] = row["student_name"]
                student_data["Branch"] = row["branch"]
                student_data["sem1_sub1_mark"] = row["sem1_sub1_mark"]
                student_data["sem1_sub2_mark"] = row["sem1_sub2_mark"]
                student_data["sem1_sub3_mark"] = row["sem1_sub3_mark"]
                student_data["sem1_sub4_mark"] = row["sem1_sub4_mark"]
                student_data["sem2_sub1_mark"] = row["sem2_sub1_mark"]
                student_data["sem2_sub2_mark"] = row["sem2_sub2_mark"]
                student_data["sem2_sub3_mark"] = row["sem2_sub3_mark"]
                student_data["sem2_sub4_mark"] = row["sem2_sub4_mark"]
                student_data["sem3_sub1_mark"] = row["sem3_sub1_mark"]
                student_data["sem3_sub2_mark"] = row["sem3_sub2_mark"]
                student_data["sem3_sub3_mark"] = row["sem3_sub3_mark"]
                student_data["sem3_sub4_mark"] = row["sem3_sub4_mark"]
                student_data["sem4_sub1_mark"] = row["sem4_sub1_mark"]
                student_data["sem4_sub2_mark"] = row["sem4_sub2_mark"]
                student_data["sem4_sub3_mark"] = row["sem4_sub3_mark"]
                student_data["sem4_sub4_mark"] = row["sem4_sub4_mark"]
                student_data["club_hours"] = row["club_hours"]
    student_data["certificate_issued"] = s.certificate_issued
    f_link = request.GET.get("file_link", None)
    student_data["file_link"] = f_link
    context = {
        "student_data": student_data,
    }
    return render(request, "student_dashboard.html", context)


def third_party(request, op=None):
    data = {"op": op}
    return render(request, "third_party.html", data)


def extract_name(f_p):
    with open(f_p, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        first_page = pdf_reader.pages[0]
        text = first_page.extract_text()
        lines = text.splitlines()
        s_name = lines[-2].strip()
    print(s_name)
    with open(f_p, "rb") as file:
        file_contents = file.read()
        hash_digest = blake3.blake3(file_contents).hexdigest()
    print(hash_digest)
    data = get_student_data_by_name(s_name)
    if data["blake3Hash"] == hash_digest:
        return True
    else:
        return False
        # print("true")


def verify_certificate(request):
    if request.method == "POST":
        if "certificate_file" in request.FILES:
            uploaded_file = request.FILES["certificate_file"]
            print("File received:", uploaded_file.name)
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            saved_file_path = fs.path(filename)
            print("File saved at:", saved_file_path)
            value = extract_name(saved_file_path)
            print(value)
            op = value
            data = {"op": op}
            return render(request, "third_party.html", data)
            # third_party(request, op=value)
    else:
        return HttpResponse("Error: File not uploaded or invalid request.", status=400)
