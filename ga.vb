Imports System.Numerics
Imports System.Threading
Imports Autodesk.AutoCAD.ApplicationServices
Imports Autodesk.AutoCAD.DatabaseServices
Imports Autodesk.AutoCAD.EditorInput
Imports Autodesk.AutoCAD.Geometry

Public Class GA

    'Hilos
    Friend syncCtrl As Windows.Forms.Control

    Public Sub BackgroundProcess()
        Thread.Sleep(GlobalVariables.ITERATION_MS)
        If syncCtrl.InvokeRequired Then
            syncCtrl.Invoke(New EjecutarDelegate(AddressOf Ejecutar))
        Else
            Ejecutar()
        End If
    End Sub

    Delegate Sub EjecutarDelegate()

    'Función ejecutar para el inicio del hilo del PSO
    Public Sub Ejecutar()
        Do
            redraw()
            GlobalVariables.NS_CONT += 1
            If GlobalVariables.NS_CONT < GlobalVariables.NS Then
                Thread.Sleep(GlobalVariables.ITERATION_MS)
            Else
                If (GlobalVariables.NI_CONT < GlobalVariables.NI) Then
                    GlobalVariables.NI_CONT += 1
                    getNewGeneration()
                    GlobalVariables.NS_CONT = 1
                    Thread.Sleep(GlobalVariables.ITERATION_MS)
                Else
                    Exit Do
                End If
            End If
        Loop
    End Sub


    'Función para inicializar el entorno del GA
    Public Sub Init()
        syncCtrl = New Windows.Forms.Control()
        syncCtrl.CreateControl()
        'Obtenemos todas los elementos y los tenemos listos para cuando queramos hacer intersecciones
        'Durante la transacción se bloquea el documento
        Using docLock As DocumentLock = GlobalVariables.doc.LockDocument()
            'Se inicia una transacción para la base de datos de AutoCAD
            Using acTrans As Transaction = GlobalVariables.db.TransactionManager.StartTransaction()
                'Obtenemos todos los elementos del documento
                Dim psr As PromptSelectionResult = GlobalVariables.ed.SelectAll()
                Dim objIds As ObjectIdCollection = New ObjectIdCollection(psr.Value.GetObjectIds())
                'Iteramos sobre el registro de bloques
                For Each objId As ObjectId In objIds
                    'Comprobamos si no es partícula
                    If GlobalVariables.dict.ContainsKey(objId.Handle) Then
                        Continue For
                    End If
                    'Si el elemento no fue partícula, obtenemos el elemento de la DB
                    Dim obj As DBObject = acTrans.GetObject(objId, OpenMode.ForWrite)
                    'Lo convertimos a objeto de tipo entidad
                    Dim ent As Entity = obj
                    'Lo agregamos a nuestra lista de entidades en variables globales
                    GlobalVariables.entities.Add(obj)
                Next
                'Guardamos la transacción en la BD
                acTrans.Commit()
                'Liberamos memoria
                acTrans.Dispose()
            End Using
        End Using
    End Sub

    'Método para ir actualizando el movimiento de las partículas
    Private Sub redraw()
        'Mover particulas
        moveParticlesOneStep()
        'Durante la transacción se bloquea el documento
        Using docLock As DocumentLock = GlobalVariables.doc.LockDocument()
            'Se inicia una transacción para la base de datos de AutoCAD
            Using acTrans As Transaction = GlobalVariables.db.TransactionManager.StartTransaction()
                Dim i As Integer = 0
                For Each p As Particula In GlobalVariables.listParticulas
                    'Creamos un punto de tipo Point3d de origen de la partícula
                    Dim poi3d As Point3d = New Point3d(p.Prev_coord1.X, p.Prev_coord1.Y, 0)
                    'Obtenemos el vector desde el origen hasta el punto de desplazamiento
                    Dim vec3d As Vector3d = poi3d.GetVectorTo(New Point3d(p.Curr_coord1.X, p.Curr_coord1.Y, 0))
                    ' Crea un objeto de tipo ObjectId
                    Dim id1 As ObjectId = GlobalVariables.db.GetObjectId(False, GlobalVariables.listHandles.Item(i), 0)
                    'Obtiene el objeto a través de una transacción
                    Dim obj1 As DBObject = acTrans.GetObject(id1, OpenMode.ForWrite)
                    'Lo convertimos a objeto de tipo círculo
                    Dim ci1 As Circle = obj1
                    'Finalmente desplazamos el círculo
                    ci1.TransformBy(Matrix3d.Displacement(vec3d))
                    GlobalVariables.doc.TransactionManager.EnableGraphicsFlush(True)
                    GlobalVariables.doc.TransactionManager.QueueForGraphicsFlush()
                    Autodesk.AutoCAD.Internal.Utils.FlushGraphics()
                    i += 1
                Next
                'Guardamos la transacción en la BD
                acTrans.Commit()
                'Liberamos memoria
                acTrans.Dispose()
            End Using
        End Using
    End Sub


    'Verdadero si intersecta un segmento de linea, definido en la particula con su punto anterior y el nuevo punto, 
    'con alguna pared.
    Public Function intersectWithWalls(p1 As Point3d, p2 As Point3d) As Boolean
        'Declaramos una línea entre ambos puntos
        Dim line As Line = New Line(p1, p2)
        'Iteramos sobre el registro de bloques
        For Each ent As Entity In GlobalVariables.entities
            'Comprobamos si no es partícula
            If GlobalVariables.dict.ContainsKey(ent.Handle) Then
                Continue For
            End If
            'Configuramos el plano tridimensional y la colección de puntos que intersectan
            Dim points As Point3dCollection = New Point3dCollection()
            'Intersectamos y almacenamos el número de puntos que intersectan en un Point3dCollection
            line.IntersectWith(ent, Intersect.OnBothOperands, points, New IntPtr(0), New IntPtr(0))
            'Validamos si al menos existe un punto de intersección
            If points.Count > 0 Then
                Return True
            End If
        Next
        Return False
    End Function

    'Saca el nuevo punto con respecto al angulo de direccion
    Public Function newPoint(point As Point3d, direction As Integer) As Point3d
        Return New Point3d(point.X + Math.Cos(direction) * GlobalVariables.ST_LEN, point.Y + Math.Sin(direction) * GlobalVariables.ST_LEN, 0)
    End Function

    'Distancia entre dos puntos.
    Public Function getDistance(p1 As Point3d, p2 As Point3d) As Double
        Return Math.Sqrt(((p1.X - p2.X) * (p1.X - p2.X)) + ((p1.Y - p2.Y) * (p1.Y - p2.Y)))
    End Function

    'Saca la distancia y si choca con alguna pared la hace grande para que la ignore
    Public Function getFitness(particle As Particula) As Integer
        Dim temp As Point3d = particle.Prev_coord1
        particle.Prev_coord1 = particle.Curr_coord1
        particle.Curr_coord1 = newPoint(particle.Curr_coord1, particle.Directions1.Item(particle.Curr_step1))
        Dim fitness_value As Double = 1000000.0 / getDistance(GlobalVariables.safe_zone, particle.Curr_coord1)
        particle.Curr_step1 += 1
        fitness_value *= fitness_value
        fitness_value *= 3.0
        If (intersectWithWalls(particle.Curr_coord1, particle.Prev_coord1) Or particle.Hitwall1) Then
            fitness_value /= 2.0
            particle.Hitwall1 = 1
            particle.Curr_coord1 = temp
        End If
        Return fitness_value
    End Function

    Public Sub moveParticlesOneStep()
        GlobalVariables.BF = -1.0
        For Each p As Particula In GlobalVariables.listParticulas
            p.Fitness1 = getFitness(p)
            If p.Fitness1 > GlobalVariables.BF Then
                GlobalVariables.BF = p.Fitness1
            End If
        Next
    End Sub

    Public Function crossover(mom As Particula, dad As Particula) As Particula
        Dim childDirections As New List(Of Integer)
        Dim cross As Integer = GlobalVariables.Generator.Next(0, GlobalVariables.NS)
        For i As Integer = 0 To GlobalVariables.NS - 1
            If i > cross Then
                childDirections.Add(mom.Directions1.Item(i))
            Else
                childDirections.Add(dad.Directions1.Item(i))

            End If
        Next
        Dim child As New Particula(GlobalVariables.start_zone.X, GlobalVariables.start_zone.Y, GlobalVariables.NS)
        child.Directions1 = childDirections
        Return child
    End Function

    Public Function mutate(child As Particula) As Particula
        For i As Integer = 0 To GlobalVariables.NS - 1
            If GlobalVariables.Generator.Next(1, 100) < GlobalVariables.MUTATIONRATE Then
                child.Directions1.Item(i) = GlobalVariables.Generator.Next(0, 360)
            End If
        Next
        Return child
    End Function

    Public Sub getNewGeneration()

        Dim nparticles As New List(Of Particula)
        Dim matingPool As New List(Of Particula)
        For i As Integer = 0 To GlobalVariables.MANYP - 1
            nparticles.Add(New Particula(GlobalVariables.start_zone.X, GlobalVariables.start_zone.Y, GlobalVariables.NS))
            Dim fitnessNormal As Double
            If GlobalVariables.listParticulas.Item(i).Fitness1 = 0 And GlobalVariables.BF = 0 Then
                fitnessNormal = 0
            Else
                fitnessNormal = Convert.ToDouble(GlobalVariables.listParticulas.Item(i).Fitness1) / Convert.ToDouble(GlobalVariables.BF)
            End If
            Dim tickets_number As New BigInteger(Math.Max(fitnessNormal * 100, 1))
            For j As BigInteger = 0 To tickets_number - 1
                matingPool.Add(GlobalVariables.listParticulas.Item(j))
            Next
        Next
        Dim matingPoolLen As Integer = matingPool.Count
        For i As Integer = 0 To GlobalVariables.MANYP - 1
            Dim m As Integer = GlobalVariables.Generator.Next(0, matingPoolLen - 1)
            Dim d As Integer = GlobalVariables.Generator.Next(0, matingPoolLen - 1)
            Dim mom As Particula = matingPool.Item(m)
            Dim dad As Particula = matingPool.Item(d)
            Dim child As Particula = crossover(mom, dad)
            child = mutate(child)
            nparticles.Item(i) = child
            nparticles.Item(i).Prev_coord1 = GlobalVariables.listParticulas.Item(i).Curr_coord1
            nparticles.Item(i).Color1 = GlobalVariables.listParticulas.Item(i).Color1
            nparticles.Item(i).Radio1 = GlobalVariables.listParticulas.Item(i).Radio1

        Next
        GlobalVariables.BF = -1.0
        GlobalVariables.listParticulas = nparticles
        redrawStartZone() 'Como las reiniciamos, las volvemos a pintar por cuestiones de AutoCAD
    End Sub

    Public Sub redrawStartZone()
        'Si ya existía una zona inicial, la modificamos de posición y color, en caso contrario la creamos.

        'Durante la transacción se bloquea el documento
        Using docLock As DocumentLock = GlobalVariables.doc.LockDocument()
            'Se inicia una transacción para la base de datos de AutoCAD
            Using acTrans As Transaction = GlobalVariables.db.TransactionManager.StartTransaction()

                'Abrimos el registro de bloques en el espacio del modelo para leer
                Dim acBlkTbl As BlockTable
                acBlkTbl = acTrans.GetObject(GlobalVariables.db.BlockTableId, OpenMode.ForRead)
                'Abrimos el registro de bloques en el espacio del modelo para escribir
                Dim acBlkTblRec As BlockTableRecord
                acBlkTblRec = acTrans.GetObject(acBlkTbl(BlockTableRecord.ModelSpace), OpenMode.ForWrite)

                'Borramos las particulas


                For Each p As Handle In GlobalVariables.listHandles
                    Dim id As ObjectId = GlobalVariables.db.GetObjectId(False, p, 0)
                    ' Abre el objeto en la DB y lo elimina
                    Dim obj As DBObject = acTrans.GetObject(id, OpenMode.ForWrite)
                    obj.Erase()
                Next
                GlobalVariables.listHandles.Clear()
                Dim x As Integer = 0
                For Each p As Particula In GlobalVariables.listParticulas
                    Dim cir As New Circle
                    cir.Center = New Point3d(p.Curr_coord1.X, p.Curr_coord1.Y, 0)
                    cir.Radius = p.Radio1
                    cir.ColorIndex = p.Color1
                    Dim obj As ObjectId = acBlkTblRec.AppendEntity(cir)
                    acTrans.AddNewlyCreatedDBObject(cir, True)
                    p.Id1 = obj.Handle()
                    GlobalVariables.listParticulasOriginal.Item(x).Id1 = obj.Handle()
                    GlobalVariables.listHandles.Add(obj.Handle())
                    x += 1
                Next
                'Guardamos la transacción en la BD
                acTrans.Commit()
                'Liberamos memoria
                acTrans.Dispose()
            End Using
        End Using

    End Sub

End Class
