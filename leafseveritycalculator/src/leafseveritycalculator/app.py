"""
This app calculates the leaf severity from a photo
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import numpy as np
from PIL import Image, ImageMath


class LeafSeverityCalculator(toga.App):
    def startup(self):
        self.img_original = None
        self.mascara_hojas = None
        self.indice = None
        self.ui_inicial = -0.03365811811
        self.ub_inicial = 185
        self.severidad = 0
        
        # Main box
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=20, background_color='#f0f0f0'))

         # Title
        title = toga.Label('Calculadora de Severidad de Hojas', style=Pack(text_align='center', font_size=24, font_weight='bold', padding=(0, 0, 20, 0)))
        main_box.add(title)

        self.photo = toga.ImageView(style=Pack(height=300, padding=5))
        camera_button = toga.Button(
            "Tomar foto",
            on_press=self.take_photo,
            style=Pack(padding=5)
        )

        self.lbl_severidad = toga.Label('Severidad: ', style=Pack(flex=1, font_size=18, font_weight='bold', text_align='center'))
        self.result = toga.ImageView(style=Pack(height=300, padding=5))

        main_box.add(camera_button)
        main_box.add(self.photo)
        main_box.add(self.lbl_severidad)
        main_box.add(self.result)

        self.main_window = toga.MainWindow(title="Calculadora de Severidad de Hojas")
        self.main_window.content = main_box
        self.main_window.show()

    async def take_photo(self, widget, **kwargs):
        try:
            if not self.camera.has_permission:
                await self.camera.request_permission()

            image = await self.camera.take_photo()
            if image:
                self.photo.image = image

                self.img_original = self.photo.image.as_format(Image.Image)

                await self.procesar_imagen()
        except NotImplementedError:
            await self.main_window.dialog(
                toga.InfoDialog(
                    "Oh no!",
                    "The Camera API is not implemented on this platform",
                )
            )
        except PermissionError:
            await self.main_window.dialog(
                toga.InfoDialog(
                    "Oh no!",
                    "You have not granted permission to take photos",
                )
            )

    async def procesar_imagen(self):
        try:
            r, g, b = Image.Image.split(self.img_original)
        except Exception as e:
            await self.main_window.dialog(
                toga.InfoDialog(
                    f"Error de split: {e}"
                )
            )

        try:
            g = np.array(g).astype(np.float32)
            r = np.array(r).astype(np.float32)
            self.indice = np.divide(
                g - r, 
                g + r + 10**(-10)#,
                #where=(g + r) != 0
                )                
        except Exception as e:
            await self.main_window.dialog(
                toga.InfoDialog(
                    f"Error al calcular el índice de enfermedad: {e}"
                )
            )

        try:
            self.mascara_hojas = np.array(b) <= self.ub_inicial
            mascara_enferma = (self.indice <= self.ui_inicial) & self.mascara_hojas
            mascara_sana = (self.indice > self.ui_inicial) & self.mascara_hojas
        except Exception as e:
            await self.main_window.dialog(
                toga.InfoDialog(
                    f"Error al calcular las máscaras: {e}"
                )
            )

        try:
            img_resultado = np.array(self.img_original.copy())
            img_resultado[~self.mascara_hojas] = [0, 0, 0]
            img_resultado[mascara_enferma] = [255, 0, 0]
            img_resultado[mascara_sana] = [0, 255, 0]

            pil_image = Image.fromarray(img_resultado.astype(np.uint8))#(img_resultado)      
            self.result.image = toga.Image(src=pil_image)
        except Exception as e:
            await self.main_window.dialog(
                toga.InfoDialog(
                    f"Error al aplicar las máscaras: {e}"
                )
            )       
            
            
        try:
            self.severidad = np.sum(mascara_enferma) / np.sum(self.mascara_hojas)
            self.lbl_severidad.text = f"Severidad: {self.severidad:.2%}"             
        except Exception as e:
            await self.main_window.dialog(
                toga.InfoDialog(
                    f"Error al calcular la severidad: {e}"
                )
            )


def main():
    return LeafSeverityCalculator()
